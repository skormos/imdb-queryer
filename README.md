# IMDB Parser / Queryer

This project parses IMDB data sources into a Postgres database to allow for more advanced queries and searches.

The data is provided for free for Non-Commercial use from [IMDB under specific terms](https://developer.imdb.com/non-commercial-datasets/).

_**THIS PROJECT IS NOT INTENDED FOR COMMERCIAL USE. ANY FORKING OF THIS PROJECT IMPLIES THAT YOU HAVE READ AND ACCEPT THESE TERMS.**_

This project:

1. Downloads IMDB data sources from https://datasets.imdbws.com/
2. Parses the downloaded sources into more clean TSV files.
3. Loads the parsed TSVs into a staging schema (`imdb_new`), removes orphaned rows, and adds constraints and indexes.
4. Swaps the staging schema in as `imdb`. The previous data stays queryable until the swap, and a failed load leaves it untouched.
5. Starts PGAdmin for easy database management.

Partly influenced from: https://gist.github.com/1mehal/13c85e108cbc906f5ec34d28d75b1968

## Maintenance Notes

Feel free to open an issue or PR if you have any questions or suggestion. That said, this project is a passive hobby,
so response and application of changes is not guaranteed.

The author takes no responsibility for how this project is used.

Credentials are currently in the clear, so currently intended for local use only.

## Steps

Everything runs in Docker; `make help` lists all commands.

First time:

1. `make refresh` downloads the IMDB files, parses them and loads them. This takes a while: the files are
   several GB and the data is NOT clean.
2. `make up` starts Postgres and PGAdmin.
3. Open PGAdmin at http://localhost:8888. The `IMDB` server is pre-registered (password `readonlypass`).
4. Bring your own DB explorer if you like, on `localhost:5433`. See Credentials below.

Day to day:

| Command        | What it does                                                                            |
|----------------|-----------------------------------------------------------------------------------------|
| `make up`      | Start Postgres and PGAdmin with the data already loaded. No downloading or loading.      |
| `make down`    | Stop everything. All data is kept.                                                      |
| `make refresh` | Download fresh IMDB files, then parse and load them. PGAdmin settings and queries are kept. |
| `make load`    | Re-parse (if needed) and load the files you already downloaded.                         |
| `make psql`    | Open `psql` as `imdbreadonly` (`make psql DB_USER=imdbowner` to write).                 |
| `make destroy` | Delete the containers, database and downloads. Keeps PGAdmin saved queries and settings. Asks first. |
| `make destroy-all` | Delete everything, including PGAdmin saved queries and settings. Asks first.        |

`docker compose --profile pipeline up` also still works as a single command: it downloads any missing files,
parses, loads and starts everything.

### Configuration

Copy `.env.example` to `.env` to change:

- `IMDB_DB_PORT` - host port for Postgres (default `5433`, so it doesn't clash with other databases on 5432).
- `PGADMIN_PORT` - host port for PGAdmin (default `8888`).
- `KEEP_PARSED` - keep the parsed TSVs (~6 GB) after a load (default `false`). Downloads are always kept.

A refresh needs room for two copies of the database while it runs (roughly 2 x 18 GB), since the old data
is only dropped after the new data is swapped in.

## Database Structure

- `title` - Contains the basic title information. `parse_sources.py` ignores Adult content. 
- `episode` - Contains episode information. `loader/sql/03_cleanup.sql` drops episodes with an orphaned series or ids in `titles`. 
- `person` - Contains person information. `parse_sources.py` drops rows without a name.
- `principal` - Contains principal information. `loader/sql/03_cleanup.sql` drops rows with an orphaned title or person.
- `rating` - Contains rating information. `loader/sql/03_cleanup.sql` drops rows with an orphaned title.

`postgres/initdb` only creates the roles, database and an empty `imdb` schema the first time Postgres starts.
The tables are created and filled by the loader (`loader/`), which can be re-run at any time.

Keep data loading out of `postgres/initdb`: Postgres only runs those scripts on an empty data volume, so anything
loaded there can't be refreshed without deleting the database (and, before this split, the PGAdmin settings with it).

The `titleType` and `genre` enums are defined in `scripts/parse_sources.py` (`TITLE_TYPES` and `GENRES`). If IMDB adds
a new value, the parse stops with a message naming it, before anything is loaded. Add the value to the list and run
`make load` again. `make check-enums` checks the downloaded files without parsing them.

Foreign keys and indexes are added to improve query performance.

## Credentials

There are five sets of credentials, one for PG Admin, the rest for the database:

1. PGAdmin: `admin@admin.org:admin` - set in the compose file.
2. Postgres Admin: `postgres:pgpass` - set in the compose file.
3. Owner Role: `imdbowner:ownerpass` - set in the `initdb` scripts.
4. Read-Write Role: `imdbreadwrite:readwritepass` - set in the `initdb` scripts.
5. Read-Only Role: `imdbreadonly:readonlypass` - set in the `initdb` scripts.`

## Scripts

- `scripts/download_sources.py` - Downloads the IMDB data sources. Existing files are kept unless `--force` is passed.
- `scripts/parse_sources.py` - Parses the downloaded sources into TSV files. Only re-parses files whose download is newer.
- `loader/load.sh` - Loads the parsed files and swaps them in.

Both Python scripts take `--source-dir` (and the parser `--target-dir`) so they can be run locally. Downloads and parsed files are
written to a temporary file first and only renamed into place once complete, so an interrupted run never leaves a
partial file that a later run would reuse.

## Development

- `make test` runs the Python unit tests (`tests/`) in Docker.
- `make lint` runs `shellcheck` on the shell scripts.

## Troubleshooting

- **Port already in use:** set `IMDB_DB_PORT` or `PGADMIN_PORT` in `.env`.
- **A load failed:** the previous data is still in place. Fix the problem and run `make load` again; a leftover
  `imdb_new` schema is dropped automatically.
- **PGAdmin doesn't show the `IMDB` server:** `pgadmin/servers.json` is only imported the first time PGAdmin
  initialises its volume. Add the server by hand (host `db`, port `5432`) or remove the `pgadmin-data` volume.

## TODOs

- [ ] Process the Title AKAs file.
- [ ] Process the Crew file.
- [ ] Configure project to read passwords from a local file.
- [ ] Test on a remote machine to run independently.
