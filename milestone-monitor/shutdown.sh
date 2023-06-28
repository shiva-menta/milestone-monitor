pkill -f 'manage.py runserver' &
pkill -f 'celery -A backend beat' &
pkill -f 'celery -A backend worker'
