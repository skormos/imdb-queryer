#!/usr/bin/env bash

set -e

echo "All initialization complete, creating flag file..."

touch /var/lib/postgresql/data/.init_complete

echo "Flag file written. Database is ready for access!"
