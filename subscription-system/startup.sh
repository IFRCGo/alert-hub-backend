python manage.py migrate
python manage.py collectstatic --no-input
python manage.py initcache
gunicorn --workers 2 --threads 4 --timeout 60 --access-logfile \
    '-' --error-logfile '-' --bind=0.0.0.0:8000 \
     --chdir=/home/site/wwwroot project.wsgi & celery -A project worker -l info -c 4 &
     celery -A project beat -l info
