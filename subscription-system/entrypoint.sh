#!/bin/bash

# wait for Postgres to start
function postgres_ready() {
python << END
import sys
import psycopg2
import os

def parse_connection_string(connection_string):
    params = connection_string.split(" ")
    params_dict = {}
    for param in params:
        key, value = param.split("=")
        params_dict[key] = value
    return params_dict

connection_string = os.getenv("AZURE_POSTGRESQL_CONNECTIONSTRING", "dbname=cap_alert host=db port=5432 sslmode=require user=1234 password=1234")
params = parse_connection_string(connection_string)

try:
    conn = psycopg2.connect(
        dbname=params["dbname"],
        user=params["user"],
        password=params["password"],
        host=params["host"],
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

python manage.py collectstatic --no-input
python manage.py migrate

exec "$@"
