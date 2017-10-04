import psef

app = psef.create_app(None, True)
celery = psef.tasks.celery
