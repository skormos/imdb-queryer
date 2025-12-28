#!/usr/bin/env python3

import argparse
import os
import requests

DOWNLOAD_FILE_EXT = 'tsv.gz'
downloadFiles = [
    'name.basics',
    'title.akas',
    'title.basics',
    'title.crew',
    'title.episode',
    'title.principals',
    'title.ratings',
]

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Parse IMDB data files')
parser.add_argument('--source-dir', default='/src/downloads', help='Source directory containing .tsv.gz files (default: /src/downloads)')
args = parser.parse_args()

source_dir = args.source_dir

if not os.path.exists(source_dir):
    os.mkdir(source_dir, mode=0o755)

for file in downloadFiles:
    file_name = f'{file}.{DOWNLOAD_FILE_EXT}'
    output_file = f'{source_dir}/{file_name}'
    if os.path.exists(f'{output_file}'):
        print(f'skipping {output_file}', flush=True)
        continue

    print(f'requesting {file_name}')
    url = f'https://datasets.imdbws.com/{file_name}'
    resp = requests.get(url, stream=True, verify=False)
    print('done requesting file')

    print(f'writing output to {output_file}')
    with open(output_file, 'wb') as tgz:
        for chunk in resp.raw.stream(1024, decode_content=False):
            if chunk:
                tgz.write(chunk)

    print('done writing file')
