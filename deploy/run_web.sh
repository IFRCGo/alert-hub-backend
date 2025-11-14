#! /bin/bash

# /code/deploy/ -> /code/
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(dirname "$BASE_DIR")

cd $ROOT_DIR

./manage.py wait_for_resources --db

./manage.py compilemessages --ignore ".venv"
uwsgi --ini ./deploy/uwsgi.ini # Start uwsgi server
