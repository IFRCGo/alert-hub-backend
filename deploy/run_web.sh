#! /bin/bash

# /code/deploy/ -> /code/
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(dirname "$BASE_DIR")

cd $ROOT_DIR

wait-for-it $DB_HOST:$DB_PORT

./manage.py collectstatic --no-input &
./manage.py compilemessages --ignore ".venv"
uwsgi --ini ./deploy/uwsgi.ini # Start uwsgi server
