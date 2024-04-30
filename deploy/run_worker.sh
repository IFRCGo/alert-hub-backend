#! /bin/bash

# /code/deploy/ -> /code/
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(dirname "$BASE_DIR")

cd $ROOT_DIR

# concurrency: Number of workers
# max-tasks-per-child: Max number of tasks a worker can run before it is terminated
celery -A main worker -l info --concurrency 4 --max-tasks-per-child 10
