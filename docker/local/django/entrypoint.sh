#!/bin/bash

set -o errexit

set -o pipefail

set -o nounset

python << END
import time
import sys
import psycopg2

suggest_unrecoverable_after = 30
start = time.time()

while True:
    try:
        psycopg2.connect(
            dbname="${POSTGRES_DB}",
            user="${POSTGRES_USER}",
            password="${POSTGRES_PASSWORD}",
            host="${POSTGRES_HOST}",
            port="${POSTGRES_PORT}",
        )
        break
    except psycopg2.OperationalError as e:
        sys.stderr.write("Waiting for postgres to become available...\n")
        if time.time() - start > suggest_unrecoverable_after:
            sys.stderr.write(
                f"Unable to connect to the database after {suggest_unrecoverable_after} seconds. "
                "This may be an unrecoverable error. Please check your database configuration and ensure that the database server is running. \n".format(e)
            )
            
        time.sleep(3)

END

echo >&2 "Postgres is available, starting the application..."

exec "$@"