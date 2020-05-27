from reciperadar.workers.broker import celery


@celery.task
def store_event(event_table, event_data):
    pass
