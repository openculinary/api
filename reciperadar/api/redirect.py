from flask import abort, redirect

from reciperadar import app
from reciperadar.models.events.redirect import RedirectEvent
from reciperadar.models.recipes import Recipe
from reciperadar.workers.events import store_event


@app.route('/api/redirect/recipe/<recipe_id>')
def recipe_redirect(recipe_id):
    recipe = Recipe().get_by_id(recipe_id)
    if not recipe:
        return abort(404)

    redirect_event = RedirectEvent(
        recipe_id=recipe.id,
        domain=recipe.domain,
        src=recipe.src
    )
    store_event.delay(
        event_table=redirect_event.__tablename__,
        event_data=redirect_event.to_doc()
    )

    return redirect(recipe.src, code=301)
