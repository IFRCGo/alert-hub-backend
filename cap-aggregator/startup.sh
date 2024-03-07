python manage.py migrate
python manage.py collectstatic --noinput
gunicorn --workers 2 --threads 4 --timeout 3000 --access-logfile \
    '-' --error-logfile '-' --bind=0.0.0.0:8000 \
     --chdir=/home/site/wwwroot capaggregator.wsgi & celery -A capaggregator worker -l info & celery -A capaggregator beat -l info