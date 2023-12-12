from reciperadar.workers.broker import celery


@celery.task(queue="index_recipe")
def index_recipe(recipe_id):
    pass


@celery.task(queue="crawl_recipe")
def crawl_recipe(url):
    pass


@celery.task(queue="crawl_url")
def crawl_url(url):
    pass
