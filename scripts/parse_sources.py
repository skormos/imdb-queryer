#!/usr/bin/env python3

import argparse
import gzip
import os.path
import sys
import traceback

EMPTY_VALUE = '\\N'


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Parse IMDB data files')
    parser.add_argument('--source-dir', default='/src/downloads',
                        help='Source directory containing .tsv.gz files (default: /src/downloads)')
    parser.add_argument('--target-dir', default='/src/parsed',
                        help='Target directory for parsed .tsv files (default: /src/parsed)')
    args = parser.parse_args()

    source_dir = args.source_dir
    target_dir = args.target_dir

    print(f'Starting parse_sources.py...', flush=True)
    print(f'Source directory: {source_dir}', flush=True)
    print(f'Target directory: {target_dir}', flush=True)

    if not os.path.exists(target_dir):
        print(f'Creating target directory: {target_dir}', flush=True)
        os.makedirs(target_dir, mode=0o755, exist_ok=True)

    if os.path.exists(f'{target_dir}/title.basics.tsv'):
        print('skipping titles...', flush=True)
    else:
        title_count = 0
        titles_included = 0
        title_types = set()
        genres = set()
        with gzip.open(f'{source_dir}/title.basics.tsv.gz', mode='rt') as tgz:
            with open(f'{target_dir}/title.basics.tsv', mode='w') as out:
                next(tgz)
                for line in tgz:
                    title_count += 1

                    fields = line.strip().split('\t')

                    title_types.add(fields[1])

                    if fields[4] == '1' or 'Adult' in fields[8]:
                        continue

                    parsed_genres = ''
                    if fields[8] != EMPTY_VALUE:
                        parsed_genres = fields[8]
                        genres.update(parsed_genres.split(','))

                    parsed_line = f'{fields[0]}\t{fields[1]}\t{fields[2]}\t{fields[3]}\t{fields[5]}\t{fields[6]}\t{fields[7]}\t{{{parsed_genres}}}\n'
                    out.write(parsed_line)
                    titles_included += 1

        print('Titles', flush=True)
        print(f'total: {title_count}', flush=True)
        print(f'included: {titles_included}', flush=True)
        print(f'types: {sorted(title_types)}', flush=True)
        print(f'genres: {sorted(genres)}', flush=True)

    if os.path.exists(f'{target_dir}/title.episode.tsv'):
        print('skipping episodes', flush=True)
    else:
        episode_count = 0
        with gzip.open(f'{source_dir}/title.episode.tsv.gz', mode='rt') as tgz:
            with open(f'{target_dir}/title.episode.tsv', mode='w') as out:
                for line in tgz.read().splitlines()[1:]:
                    episode_count += 1

                    fields = line.strip().split('\t')

                    out.write(f'{fields[0]}\t{fields[1]}\t{fields[2]}\t{fields[3]}\n')

        print('Episodes', flush=True)
        print(f'total: {episode_count}', flush=True)

    if os.path.exists(f'{target_dir}/title.principals.tsv'):
        print('skipping principals', flush=True)
    else:
        principal_count = 0
        with gzip.open(f'{source_dir}/title.principals.tsv.gz', mode='rt') as tgz:
            with open(f'{target_dir}/title.principals.tsv', mode='w') as out:
                next(tgz)
                for line in tgz:
                    principal_count += 1

                    if principal_count % 100000 == 0:
                        print(f'Processed {principal_count} principals...', flush=True)

                    fields = line.strip().split('\t')

                    out.write(f'{fields[0]}\t{fields[1]}\t{fields[2]}\t{fields[3]}\t{fields[4]}\t{fields[5]}\n')

        print('Principals', flush=True)
        print(f'total: {principal_count}', flush=True)

    if os.path.exists(f'{target_dir}/name.basics.tsv'):
        print('skipping persons', flush=True)
    else:
        persons_count = 0
        persons_included = 0
        with gzip.open(f'{source_dir}/name.basics.tsv.gz', mode='rt') as tgz:
            with open(f'{target_dir}/name.basics.tsv', mode='w') as out:
                next(tgz)
                for line in tgz:
                    persons_count += 1
                    fields = line.strip().split('\t')

                    if fields[1] == EMPTY_VALUE:
                        continue

                    out.write(f'{fields[0]}\t{fields[1]}\t{fields[2]}\t{fields[3]}\t{fields[4]}\n')
                    persons_included += 1

        print('Persons', flush=True)
        print(f'total: {persons_count}', flush=True)
        print(f'included: {persons_included}', flush=True)

    if os.path.exists(f'{target_dir}/title.ratings.tsv'):
        print('skipping ratings', flush=True)
    else:
        ratings_count = 0
        with gzip.open(f'{source_dir}/title.ratings.tsv.gz', mode='rt') as tgz:
            with open(f'{target_dir}/title.ratings.tsv', mode='w') as out:
                next(tgz)
                for line in tgz:
                    ratings_count += 1

                    fields = line.strip().split('\t')

                    out.write(f'{fields[0]}\t{fields[1]}\t{fields[2]}\n')

        print('Ratings', flush=True)
        print(f'total: {ratings_count}', flush=True)

    print('Parse completed successfully!', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: An unexpected error occurred!', file=sys.stderr, flush=True)
        print(f'ERROR: {type(e).__name__}: {str(e)}', file=sys.stderr, flush=True)
        print('ERROR: Full traceback:', file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)