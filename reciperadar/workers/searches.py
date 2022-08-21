from reciperadar.workers.broker import celery


@celery.task(queue="recrawl_search")
def recrawl_search(include, exclude, equipment, dietary_properties, offset):
    pass
