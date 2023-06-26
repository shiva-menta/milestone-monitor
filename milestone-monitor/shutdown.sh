echo "Shutting down Django runserver..."
pkill -f "manage.py runserver"

echo "Shutting down Celery beat..."
pkill -f "celery -A backend beat"

echo "Shutting down Celery worker..."
pkill -f "celery -A backend worker"

echo "Shutdown complete."