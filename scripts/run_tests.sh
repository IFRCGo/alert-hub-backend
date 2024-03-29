#!/bin/bash -x

export PYTHONUNBUFFERED=1
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$(dirname "$BASE_DIR")

# Wait until database is ready
wait-for-it ${DB_HOST:-db}:${DB_PORT-5432}

if [ "$CI" == "true" ]; then
    pip3 install coverage pytest-xdist

    set -e
    # To show migration logs
    ./manage.py test --keepdb -v 2 main.tests.test_fake

    # Run all tests now
    echo 'import coverage; coverage.process_startup()' > /code/sitecustomize.py
    COVERAGE_PROCESS_START=`pwd`/.coveragerc COVERAGE_FILE=`pwd`/.coverage PYTHONPATH=`pwd` py.test --reuse-db --dist=loadfile --durations=10
    rm /code/sitecustomize.py

    # Collect/Generate reports
    coverage combine
    coverage report -i
    coverage html -i
    coverage xml

    mkdir -p $ROOT_DIR/coverage/
    mv htmlcov $ROOT_DIR/coverage/
    mv coverage.xml $ROOT_DIR/coverage/

    set +e
else
    py.test
fi
