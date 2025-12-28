# IMDB Parser / Queryer

This project parses IMDB data sources into a Postgres database to allow for more advanced queries and searches.

The data is provided for free for Non-Commercial use from [IMDB under specific terms](https://developer.imdb.com/non-commercial-datasets/).

_**THIS PROJECT IS NOT INTENDED FOR COMMERCIAL USE. ANY FORKING OF THIS PROJECT IMPLIES THAT YOU HAVE READ AND ACCEPT THESE TERMS.**_

This project:

1. Downloads IMDB data sources from https://datasets.imdbws.com/
2. Parses the downloaded sources into more clean TSV files.
3. Creates the database schema without contraints.
4. Copies the parsed TSVs to the tables.
5. Performs additional cleanup to remove orphaned data.
6. Applies constraints to the tables.
7. Starts PGAdmin for easy database management.

Partly influenced from: https://gist.github.com/1mehal/13c85e108cbc906f5ec34d28d75b1968

## Maintenance Notes

Feel free to open an issue or PR if you have any questions or suggestion. That said, this project is a passive hobby,
so response and application of changes is not guaranteed.

The author takes no responsibility for how this project is used.

Credentials are currently in the clear, so currently intended for local use only.

## Steps

1. Run `docker-compose up`.
2. Wait until PGAdmin is available. This will take at least 5 minutes as the data needs to be parsed and loaded and then constraints applied, and the data is NOT clean.
3. Use PGAdmin to explore the data.
4. Bring your own DB explorer if you like. See Credentials below.

## Database Structure

- `title` - Contains the basic title information. `parse_sources.py` ignores Adult content. 
- `episode` - Contains episode information. `initdb/load_data.sh` drops episodes with an orphaned series or ids in `titles`. 
- `person` - Contains person information. `parse_sources.py` drops rows without a name.
- `principal` - Contains principal information. `initdb/load_data.sh` drops rows with an orphaned title or person.
- `rating` - Contains rating information. `initdb/load_data.sh` drops rows with an orphaned title.

Foreign keys and indexes are added to improve query performance.

## Credentials

There are five sets of credentials, one for PG Admin, the rest for the database:

1. PGAdmin: `admin@admin.org:admin` - set in the compose file.
2. Postgres Admin: `postgres:pgpass` - set in the compose file.
3. Owner Role: `imdbowner:ownerpass` - set in the `initdb` scripts.
4. Read-Write Role: `imdbreadwrite:readwritepass` - set in the `initdb` scripts.
5. Read-Only Role: `imdbreadonly:readonlypass` - set in the `initdb` scripts.`

## Scripts

- `scripts/download_sources.py` - Downloads the IMDB data sources.
- `scripts/parse_sources.py` - Parses the downloaded sources into TSV files.

Both scripts can be configured to run locally for testing purposes. See the scripts for details.

## Troubleshooting

If `docker compose up` fails due to a timeout, wait a few minutes, run `docker ps -a` to see if the `db` container is healthy, and then run `docker compose up` again.

## TODOs

- [ ] Process the Title AKAs file.
- [ ] Process the Crew file.
- [ ] Configure project to read passwords from a local file.
- [ ] Test on a remote machine to run independently.
