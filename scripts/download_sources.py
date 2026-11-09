#!/usr/bin/env python3
"""Download the IMDB non-commercial datasets.

Existing files are kept unless --force is given. Each file is downloaded to a
``.part`` file and only renamed into place once it is complete and looks like
gzip, so an interrupted or failed download never replaces a good file.
"""

import argparse
import os
import sys
from pathlib import Path

import requests

BASE_URL = 'https://datasets.imdbws.com'
DOWNLOAD_FILE_EXT = 'tsv.gz'
DOWNLOAD_FILES = [
    'name.basics',
    'title.akas',
    'title.basics',
    'title.crew',
    'title.episode',
    'title.principals',
    'title.ratings',
]
CHUNK_SIZE = 1024 * 1024
GZIP_MAGIC = b'\x1f\x8b'
# (connect, read) timeouts in seconds. The read timeout is per chunk, not for the whole file.
TIMEOUT = (10, 60)


def download(session: requests.Session, url: str, dest: Path) -> None:
    part = dest.with_name(dest.name + '.part')
    try:
        with session.get(url, stream=True, timeout=TIMEOUT) as resp:
            resp.raise_for_status()
            with open(part, 'wb') as out:
                # decode_content=False: keep the bytes exactly as served (they are the .gz file).
                for chunk in resp.raw.stream(CHUNK_SIZE, decode_content=False):
                    out.write(chunk)

        with open(part, 'rb') as f:
            if f.read(2) != GZIP_MAGIC:
                raise ValueError(f'{url} did not return a gzip file')

        os.replace(part, dest)
    except BaseException:
        part.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Download IMDB data files')
    parser.add_argument('--source-dir', type=Path, default=Path('/src/downloads'),
                        help='Directory to write the .tsv.gz files to (default: /src/downloads)')
    parser.add_argument('--force', action='store_true',
                        help='Download fresh copies even if the files already exist')
    args = parser.parse_args(argv)

    args.source_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

    with requests.Session() as session:
        for name in DOWNLOAD_FILES:
            file_name = f'{name}.{DOWNLOAD_FILE_EXT}'
            dest = args.source_dir / file_name
            if dest.exists() and not args.force:
                print(f'{file_name}: already downloaded, skipping (use --force to refresh)', flush=True)
                continue

            url = f'{BASE_URL}/{file_name}'
            print(f'{file_name}: downloading {url}', flush=True)
            download(session, url, dest)
            print(f'{file_name}: done ({dest.stat().st_size / 1024 / 1024:.0f} MiB)', flush=True)

    print('Downloads complete.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}', file=sys.stderr, flush=True)
        sys.exit(1)
