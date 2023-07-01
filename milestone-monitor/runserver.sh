python manage.py runserver &
python -m celery -A backend beat -l info --logfile=celery.beat.log --detach &
python -m celery -A backend worker -l info --logfile=celery.worker.log --detach --concurrency 4