import gzip
import os

import pytest

import parse_sources as ps

TITLE_HEADER = 'tconst\ttitleType\tprimaryTitle\toriginalTitle\tisAdult\tstartYear\tendYear\truntimeMinutes\tgenres\n'
EPISODE_HEADER = 'tconst\tparentTconst\tseasonNumber\tepisodeNumber\n'
PRINCIPAL_HEADER = 'tconst\tordering\tnconst\tcategory\tjob\tcharacters\n'
PERSON_HEADER = 'nconst\tprimaryName\tbirthYear\tdeathYear\tprimaryProfession\tknownForTitles\n'
RATING_HEADER = 'tconst\taverageRating\tnumVotes\n'


def row(*fields: str) -> str:
    return '\t'.join(fields) + '\n'


def run(transform, lines):
    stats = ps.Stats(label='test')
    return list(transform(lines, stats)), stats


# --- titles -----------------------------------------------------------------

def title(tconst='tt1', ttype='movie', primary='A Movie', original='A Movie', adult='0',
          start='1999', end='\\N', runtime='90', genres='Drama'):
    return row(tconst, ttype, primary, original, adult, start, end, runtime, genres)


def test_titles_skips_header_and_drops_is_adult_column():
    out, stats = run(ps.transform_titles, [TITLE_HEADER, title()])

    assert out == [row('tt1', 'movie', 'A Movie', 'A Movie', '1999', '\\N', '90', '{Drama}')]
    assert (stats.total, stats.included) == (1, 1)


@pytest.mark.parametrize('genres, want', [
    ('\\N', '{}'),
    ('Drama', '{Drama}'),
    ('Comedy,Sci-Fi,Film-Noir', '{Comedy,Sci-Fi,Film-Noir}'),
])
def test_titles_genres_become_array_literal(genres, want):
    out, _ = run(ps.transform_titles, [TITLE_HEADER, title(genres=genres)])

    assert out[0].rstrip('\n').split('\t')[-1] == want


@pytest.mark.parametrize('adult, genres', [('1', 'Drama'), ('0', 'Adult'), ('0', 'Drama,Adult')])
def test_titles_drops_adult(adult, genres):
    out, stats = run(ps.transform_titles, [TITLE_HEADER, title(adult=adult, genres=genres)])

    assert out == []
    assert stats.extra['adult skipped'] == 1


def test_titles_keeps_awkward_text_intact():
    awkward = ' "Quoted" \\ back\\slash, üñíçødé '
    out, _ = run(ps.transform_titles, [TITLE_HEADER, title(primary=awkward, original=awkward)])

    fields = out[0].rstrip('\n').split('\t')
    assert fields[2] == awkward
    assert fields[3] == awkward


def test_titles_skips_malformed_rows():
    out, stats = run(ps.transform_titles, [TITLE_HEADER, 'tt1\tmovie\tshort row\n', title(tconst='tt2')])

    assert [line.split('\t')[0] for line in out] == ['tt2']
    assert stats.malformed == 1


def test_empty_input_produces_nothing():
    out, stats = run(ps.transform_titles, [])

    assert out == []
    assert stats.total == 0


# --- enum drift ---------------------------------------------------------------

def test_titles_unknown_type_raises_after_reading_everything():
    lines = [TITLE_HEADER, title(tconst='tt1', ttype='podcast'), title(tconst='tt2', ttype='hologram')]

    with pytest.raises(ps.EnumDriftError) as exc:
        run(ps.transform_titles, lines)

    assert exc.value.unknown_types == {'podcast', 'hologram'}
    assert exc.value.unknown_genres == set()
    assert 'TITLE_TYPES' in str(exc.value)


def test_titles_unknown_genre_raises():
    with pytest.raises(ps.EnumDriftError) as exc:
        run(ps.transform_titles, [TITLE_HEADER, title(genres='Drama,Cyberpunk')])

    assert exc.value.unknown_genres == {'Cyberpunk'}


def test_unknown_values_on_adult_titles_are_ignored():
    out, _ = run(ps.transform_titles, [TITLE_HEADER, title(ttype='podcast', adult='1')])

    assert out == []


def test_types_sql_lists_every_enum_value():
    sql = ps.types_sql()

    for value in ps.TITLE_TYPES + ps.GENRES:
        assert f"'{value}'" in sql
    assert 'CREATE TYPE titleType AS ENUM' in sql
    assert 'CREATE TYPE genre AS ENUM' in sql


def test_enum_lists_have_no_duplicates():
    assert len(set(ps.TITLE_TYPES)) == len(ps.TITLE_TYPES)
    assert len(set(ps.GENRES)) == len(ps.GENRES)
    assert 'Adult' not in ps.GENRES  # adult titles are filtered out, never loaded


# --- other datasets -----------------------------------------------------------

def test_episodes_pass_through():
    lines = [EPISODE_HEADER, row('tt2', 'tt1', '1', '3'), row('tt3', 'tt1', '\\N', '\\N')]

    out, stats = run(ps.transform_episodes, lines)

    assert out == lines[1:]
    assert stats.included == 2


def test_principals_pass_through_with_json_characters():
    lines = [PRINCIPAL_HEADER, row('tt1', '1', 'nm1', 'actor', '\\N', '["Self", "Narrator"]')]

    out, _ = run(ps.transform_principals, lines)

    assert out == lines[1:]


def test_persons_drop_unnamed_and_known_for_column():
    lines = [
        PERSON_HEADER,
        row('nm1', 'Jane Doe', '1950', '\\N', 'actress,producer', 'tt1,tt2'),
        row('nm2', '\\N', '\\N', '\\N', '\\N', '\\N'),
    ]

    out, stats = run(ps.transform_persons, lines)

    assert out == [row('nm1', 'Jane Doe', '1950', '\\N', 'actress,producer')]
    assert (stats.total, stats.included) == (2, 1)


def test_ratings_pass_through():
    lines = [RATING_HEADER, row('tt1', '7.5', '1234')]

    out, _ = run(ps.transform_ratings, lines)

    assert out == lines[1:]


# --- files --------------------------------------------------------------------

def write_gz(path, text):
    with gzip.open(path, 'wt', encoding='utf-8', newline='\n') as f:
        f.write(text)


def test_carriage_return_inside_field_does_not_split_row(tmp_path):
    src = tmp_path / 'title.basics.tsv.gz'
    write_gz(src, TITLE_HEADER + title(primary='Line\rBreak'))

    with ps.open_source(src) as f:
        out, stats = run(ps.transform_titles, f)

    assert stats.malformed == 0
    assert out[0].split('\t')[2] == 'Line\rBreak'


def test_parse_dataset_writes_output_and_skips_when_up_to_date(tmp_path):
    src_dir, dst_dir = tmp_path / 'src', tmp_path / 'dst'
    src_dir.mkdir()
    dst_dir.mkdir()
    write_gz(src_dir / 'title.ratings.tsv.gz', RATING_HEADER + row('tt1', '7.5', '10'))

    ps.parse_dataset('title.ratings', ps.transform_ratings, src_dir, dst_dir, force=False)
    target = dst_dir / 'title.ratings.tsv'
    assert target.read_text() == row('tt1', '7.5', '10')

    # Up to date: a second run must not rewrite the file.
    target.write_text('sentinel')
    ps.parse_dataset('title.ratings', ps.transform_ratings, src_dir, dst_dir, force=False)
    assert target.read_text() == 'sentinel'

    # --force re-parses.
    ps.parse_dataset('title.ratings', ps.transform_ratings, src_dir, dst_dir, force=True)
    assert target.read_text() == row('tt1', '7.5', '10')


def test_parse_dataset_reparses_when_download_is_newer(tmp_path):
    write_gz(tmp_path / 'title.ratings.tsv.gz', RATING_HEADER + row('tt1', '9.9', '1'))
    target = tmp_path / 'title.ratings.tsv'
    target.write_text('stale')
    old = (tmp_path / 'title.ratings.tsv.gz').stat().st_mtime - 60
    os.utime(target, (old, old))

    ps.parse_dataset('title.ratings', ps.transform_ratings, tmp_path, tmp_path, force=False)

    assert target.read_text() == row('tt1', '9.9', '1')


def test_failed_parse_leaves_no_output_behind(tmp_path):
    write_gz(tmp_path / 'title.basics.tsv.gz', TITLE_HEADER + title(ttype='podcast'))

    with pytest.raises(ps.EnumDriftError):
        ps.parse_dataset('title.basics', ps.transform_titles, tmp_path, tmp_path, force=False)

    assert not (tmp_path / 'title.basics.tsv').exists()
    assert not (tmp_path / 'title.basics.tsv.tmp').exists()


def test_failed_parse_keeps_previous_output(tmp_path):
    target = tmp_path / 'title.basics.tsv'
    target.write_text('previous good output')
    write_gz(tmp_path / 'title.basics.tsv.gz', TITLE_HEADER + title(ttype='podcast'))

    with pytest.raises(ps.EnumDriftError):
        ps.parse_dataset('title.basics', ps.transform_titles, tmp_path, tmp_path, force=True)

    assert target.read_text() == 'previous good output'


def test_check_enums_reports_drift(tmp_path):
    write_gz(tmp_path / 'title.basics.tsv.gz', TITLE_HEADER + title(genres='Cyberpunk'))

    with pytest.raises(ps.EnumDriftError):
        ps.check_enums(tmp_path)


def test_main_writes_all_outputs(tmp_path):
    src, dst = tmp_path / 'downloads', tmp_path / 'parsed'
    src.mkdir()
    write_gz(src / 'title.basics.tsv.gz', TITLE_HEADER + title())
    write_gz(src / 'title.episode.tsv.gz', EPISODE_HEADER + row('tt2', 'tt1', '1', '1'))
    write_gz(src / 'title.principals.tsv.gz', PRINCIPAL_HEADER + row('tt1', '1', 'nm1', 'actor', '\\N', '\\N'))
    write_gz(src / 'name.basics.tsv.gz', PERSON_HEADER + row('nm1', 'Jane', '\\N', '\\N', '\\N', '\\N'))
    write_gz(src / 'title.ratings.tsv.gz', RATING_HEADER + row('tt1', '7.0', '5'))

    ps.main(['--source-dir', str(src), '--target-dir', str(dst)])

    assert sorted(p.name for p in dst.iterdir()) == [
        'name.basics.tsv', 'title.basics.tsv', 'title.episode.tsv',
        'title.principals.tsv', 'title.ratings.tsv', 'types.sql',
    ]
