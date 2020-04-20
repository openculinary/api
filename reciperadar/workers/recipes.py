from sqlalchemy.orm import aliased

from reciperadar.models.recipes import Recipe
from reciperadar.models.url import CrawlURL, RecipeURL
from reciperadar.services.database import Database
from reciperadar.workers.broker import celery


@celery.task(queue='index_recipe')
def index_recipe(recipe_id):
    session = Database().get_session()
    recipe = session.query(Recipe).get(recipe_id)
    if not recipe:
        print('Could not find recipe to index')
        session.close()
        return

    if recipe.index():
        print(f'Indexed {recipe.id} for url={recipe.src}')
        session.commit()

    session.close()


@celery.task(queue='process_recipe')
def process_recipe(recipe_id):
    session = Database().get_session()
    recipe = session.query(Recipe).get(recipe_id)
    if not recipe:
        print('Could not find recipe to process')
        session.close()
        return

    index_recipe.delay(recipe.id)
    session.close()


def find_earliest_crawl(session, url):
    earliest_crawl = (
        session.query(
            CrawlURL.crawled_at,
            CrawlURL.url,
            CrawlURL.resolves_to
        )
        .filter_by(resolves_to=url)
        .cte(recursive=True)
    )

    previous_step = aliased(earliest_crawl)
    earliest_crawl = earliest_crawl.union_all(
        session.query(
            CrawlURL.crawled_at,
            CrawlURL.url,
            previous_step.c.url
        )
        .filter_by(resolves_to=previous_step.c.url)
        .filter(CrawlURL.resolves_to != previous_step.c.resolves_to)
    )

    return (
        session.query(earliest_crawl)
        .order_by(earliest_crawl.c.crawled_at.asc())
        .first()
    )


def find_latest_crawl(session, url):
    latest_crawl = (
        session.query(
            CrawlURL.crawled_at,
            CrawlURL.url,
            CrawlURL.resolves_to
        )
        .filter_by(resolves_to=url)
        .cte(recursive=True)
    )

    previous_step = aliased(latest_crawl)
    latest_crawl = latest_crawl.union_all(
        session.query(
            CrawlURL.crawled_at,
            CrawlURL.url,
            previous_step.c.url
        )
        .filter_by(url=previous_step.c.resolves_to)
        .filter(CrawlURL.resolves_to != previous_step.c.resolves_to)
    )

    return (
        session.query(latest_crawl)
        .order_by(latest_crawl.c.crawled_at.desc())
        .first()
    )


@celery.task(queue='crawl_recipe')
def crawl_recipe(url):
    session = Database().get_session()
    recipe_url = session.query(RecipeURL).get(url) or RecipeURL(url=url)

    try:
        response = recipe_url.crawl()
    except RecipeURL.BackoffException:
        print(f'Backoff: {recipe_url.error_message} for url={url}')
        return
    except Exception:
        print(f'{recipe_url.error_message} for url={url}')
        return
    finally:
        session.add(recipe_url)
        session.commit()
        session.close()

    if not response.ok:
        return

    try:
        recipe_data = response.json()
    except Exception as e:
        print(f'Failed to load crawler result for url={url} - {e}')
        return

    session = Database().get_session()

    # Find any more-recent crawls of this URL, allowing detection of duplicates
    latest_crawl = find_latest_crawl(session, url)

    # Find the first-known crawl for the latest URL, and consider it the origin
    earliest_crawl = find_earliest_crawl(session, latest_crawl.url)

    recipe_data['src'] = earliest_crawl.url
    recipe_data['dst'] = latest_crawl.url
    recipe = Recipe.from_doc(recipe_data)

    session.query(Recipe).filter_by(id=recipe.id).delete()
    session.add(recipe)
    session.commit()

    process_recipe.delay(recipe.id)
    session.close()


@celery.task(queue='crawl_url')
def crawl_url(url):
    session = Database().get_session()
    crawl_url = session.query(CrawlURL).get(url) or CrawlURL(url=url)

    try:
        response = crawl_url.crawl()
        url = crawl_url.resolves_to
    except RecipeURL.BackoffException:
        print(f'Backoff: {crawl_url.error_message} for url={crawl_url.url}')
        return
    except Exception:
        print(f'{crawl_url.error_message} for url={crawl_url.url}')
        return
    finally:
        session.add(crawl_url)
        session.commit()
        session.close()

    if not response.ok:
        return

    session = Database().get_session()
    recipe_url = session.query(RecipeURL).get(url) or RecipeURL(url=url)
    session.add(recipe_url)
    session.commit()
    session.close()

    crawl_recipe.delay(url)
