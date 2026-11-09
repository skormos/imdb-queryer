#!/usr/bin/env python3
"""Parse the raw IMDB .tsv.gz downloads into clean TSVs ready for Postgres COPY.

Each dataset has a pure ``transform_*`` function (lines in, lines out) so it can
be unit tested without touching the filesystem. Output files are written
atomically: a crash mid-parse never leaves a truncated file behind that a later
run would mistake for a finished one.
"""

import argparse
import contextlib
import gzip
import os
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Iterator

EMPTY_VALUE = '\\N'
MAX_MALFORMED_REPORTS = 5
PROGRESS_EVERY = 1_000_000

# These lists are the single source of truth for the Postgres enum types.
# The parser writes them to types.sql, which the loader runs before creating tables.
# If IMDB adds a new value the parse fails with a clear message: add it here.
TITLE_TYPES = (
    'movie', 'short', 'tvEpisode', 'tvMiniSeries', 'tvMovie', 'tvPilot',
    'tvSeries', 'tvShort', 'tvSpecial', 'video', 'videoGame',
)
GENRES = (
    'Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime',
    'Documentary', 'Drama', 'Family', 'Fantasy', 'Film-Noir', 'Game-Show',
    'History', 'Horror', 'Music', 'Musical', 'Mystery', 'News', 'Reality-TV',
    'Romance', 'Sci-Fi', 'Short', 'Sport', 'Talk-Show', 'Thriller', 'War',
    'Western',
)


class EnumDriftError(ValueError):
    """IMDB data contains title types or genres that the schema does not know about."""

    def __init__(self, unknown_types: set[str], unknown_genres: set[str]):
        self.unknown_types = unknown_types
        self.unknown_genres = unknown_genres
        parts = []
        if unknown_types:
            parts.append(f'unknown title types: {sorted(unknown_types)}')
        if unknown_genres:
            parts.append(f'unknown genres: {sorted(unknown_genres)}')
        super().__init__(
            '; '.join(parts)
            + '. Add them to TITLE_TYPES / GENRES in scripts/parse_sources.py and re-run.'
        )


@dataclass
class Stats:
    total: int = 0
    included: int = 0
    malformed: int = 0
    label: str = ''
    extra: dict = field(default_factory=dict)

    def report(self) -> str:
        lines = [f'{self.label}: total={self.total} included={self.included} malformed={self.malformed}']
        lines += [f'  {k}: {v}' for k, v in self.extra.items()]
        return '\n'.join(lines)


def _rows(lines: Iterable[str], expected_fields: int, stats: Stats) -> Iterator[list[str]]:
    """Yield the tab-split fields of each data row.

    Skips the header row, and skips (and counts) rows with the wrong number of fields.
    """
    it = iter(lines)
    next(it, None)  # header
    for line_no, line in enumerate(it, start=2):
        stats.total += 1
        if stats.total % PROGRESS_EVERY == 0:
            print(f'  {stats.label}: processed {stats.total} rows...', flush=True)

        # Only strip the newline: whitespace at the edges of a field is data.
        fields = line.rstrip('\n').split('\t')
        if len(fields) != expected_fields:
            stats.malformed += 1
            if stats.malformed <= MAX_MALFORMED_REPORTS:
                print(f'  WARNING {stats.label} line {line_no}: expected {expected_fields} fields, '
                      f'got {len(fields)}; skipping: {line[:200]!r}', flush=True)
            continue
        yield fields


def _join(*fields: str) -> str:
    return '\t'.join(fields) + '\n'


def transform_titles(lines: Iterable[str], stats: Stats) -> Iterator[str]:
    """title.basics: drop adult titles, convert genres to a Postgres array literal.

    Raises EnumDriftError (after consuming all input) if any included title has a
    type or genre that is not in TITLE_TYPES / GENRES.
    """
    known_types, known_genres = set(TITLE_TYPES), set(GENRES)
    unknown_types: set[str] = set()
    unknown_genres: set[str] = set()
    adult = 0

    for f in _rows(lines, 9, stats):
        tconst, title_type, primary, original, is_adult, start, end, runtime, genres = f
        genre_list = [] if genres == EMPTY_VALUE else genres.split(',')

        if is_adult == '1' or 'Adult' in genre_list:
            adult += 1
            continue

        if title_type not in known_types:
            unknown_types.add(title_type)
        unknown_genres.update(g for g in genre_list if g not in known_genres)

        stats.included += 1
        yield _join(tconst, title_type, primary, original, start, end, runtime,
                    '{' + ','.join(genre_list) + '}')

    stats.extra['adult skipped'] = adult
    if unknown_types or unknown_genres:
        raise EnumDriftError(unknown_types, unknown_genres)


def transform_episodes(lines: Iterable[str], stats: Stats) -> Iterator[str]:
    """title.episode: passed through as-is (id, series id, season, episode)."""
    for f in _rows(lines, 4, stats):
        stats.included += 1
        yield _join(*f)


def transform_principals(lines: Iterable[str], stats: Stats) -> Iterator[str]:
    """title.principals: passed through as-is."""
    for f in _rows(lines, 6, stats):
        stats.included += 1
        yield _join(*f)


def transform_persons(lines: Iterable[str], stats: Stats) -> Iterator[str]:
    """name.basics: drop people without a name, and the knownForTitles column."""
    for nconst, name, birth, death, professions, _known_for in _rows(lines, 6, stats):
        if name == EMPTY_VALUE:
            continue
        stats.included += 1
        yield _join(nconst, name, birth, death, professions)


def transform_ratings(lines: Iterable[str], stats: Stats) -> Iterator[str]:
    """title.ratings: passed through as-is."""
    for f in _rows(lines, 3, stats):
        stats.included += 1
        yield _join(*f)


Transform = Callable[[Iterable[str], Stats], Iterator[str]]

DATASETS: dict[str, Transform] = {
    'title.basics': transform_titles,
    'title.episode': transform_episodes,
    'title.principals': transform_principals,
    'name.basics': transform_persons,
    'title.ratings': transform_ratings,
}


def types_sql() -> str:
    """CREATE TYPE statements for the enums (unqualified: the loader sets search_path)."""
    def enum(values: tuple[str, ...]) -> str:
        return ', '.join(f"'{v}'" for v in values)

    return (
        f'CREATE TYPE titleType AS ENUM ({enum(TITLE_TYPES)});\n'
        f'CREATE TYPE genre AS ENUM ({enum(GENRES)});\n'
    )


@contextlib.contextmanager
def atomic_write(path: Path):
    """Open ``path`` for writing via a temp file that is only renamed into place on success."""
    tmp = path.with_name(path.name + '.tmp')
    try:
        with open(tmp, 'w', encoding='utf-8', newline='\n') as out:
            yield out
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def open_source(path: Path):
    # newline='\n': only \n ends a row. The default would also split on a stray \r inside a field.
    return gzip.open(path, mode='rt', encoding='utf-8', newline='\n')


def is_up_to_date(source: Path, target: Path) -> bool:
    return target.exists() and target.stat().st_mtime >= source.stat().st_mtime


def parse_dataset(name: str, transform: Transform, source_dir: Path, target_dir: Path, force: bool) -> None:
    source = source_dir / f'{name}.tsv.gz'
    target = target_dir / f'{name}.tsv'

    if not source.exists():
        raise FileNotFoundError(f'{source} not found. Run the downloader first (make download).')

    if not force and is_up_to_date(source, target):
        print(f'{name}: up to date, skipping', flush=True)
        return

    print(f'{name}: parsing {source} -> {target}', flush=True)
    stats = Stats(label=name)
    with open_source(source) as src, atomic_write(target) as out:
        out.writelines(transform(src, stats))
    print(stats.report(), flush=True)


def check_enums(source_dir: Path) -> None:
    """Scan title.basics for enum drift without writing anything."""
    stats = Stats(label='title.basics')
    with open_source(source_dir / 'title.basics.tsv.gz') as src:
        for _ in transform_titles(src, stats):
            pass
    print(stats.report(), flush=True)
    print('All title types and genres are known.', flush=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Parse IMDB data files')
    parser.add_argument('--source-dir', type=Path, default=Path('/src/downloads'),
                        help='Directory containing the .tsv.gz downloads (default: /src/downloads)')
    parser.add_argument('--target-dir', type=Path, default=Path('/src/parsed'),
                        help='Directory for the parsed .tsv files (default: /src/parsed)')
    parser.add_argument('--force', action='store_true',
                        help='Re-parse even if the parsed file is newer than its download')
    parser.add_argument('--check-enums', action='store_true',
                        help='Only check title.basics for unknown title types / genres, then exit')
    args = parser.parse_args(argv)

    if args.check_enums:
        check_enums(args.source_dir)
        return

    print(f'Source directory: {args.source_dir}', flush=True)
    print(f'Target directory: {args.target_dir}', flush=True)
    args.target_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

    with atomic_write(args.target_dir / 'types.sql') as out:
        out.write(types_sql())

    for name, transform in DATASETS.items():
        parse_dataset(name, transform, args.source_dir, args.target_dir, args.force)

    print('Parse completed successfully!', flush=True)


if __name__ == '__main__':
    try:
        main()
    except EnumDriftError as e:
        print(f'ERROR: schema drift in IMDB data: {e}', file=sys.stderr, flush=True)
        sys.exit(2)
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}', file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
