from reciperadar import db
from reciperadar.models.base import Searchable, Storable
from reciperadar.models.recipes.direction import RecipeDirection
from reciperadar.models.recipes.ingredient import RecipeIngredient
from reciperadar.models.recipes.nutrition import IngredientNutrition


class Recipe(Storable, Searchable):
    __tablename__ = 'recipes'

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    src = db.Column(db.String)
    dst = db.Column(db.String)
    domain = db.Column(db.String)
    author = db.Column(db.String)
    author_url = db.Column(db.String)
    image_src = db.Column(db.String)
    time = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    rating = db.Column(db.Float)
    nutrition = db.Column(db.JSON)
    ingredients = db.relationship(
        'RecipeIngredient',
        backref='recipe',
        passive_deletes='all'
    )
    directions = db.relationship(
        'RecipeDirection',
        backref='recipe',
        passive_deletes='all'
    )

    indexed_at = db.Column(db.DateTime)

    @property
    def noun(self):
        return 'recipes'

    @property
    def url(self):
        return f'/#action=view&id={self.id}'

    @property
    def products(self):
        unique_products = {
            ingredient.product.singular: ingredient.product
            for ingredient in self.ingredients
        }
        return list(unique_products.values())

    @property
    def hidden(self):
        for ingredient in self.ingredients:
            if not ingredient.product.singular:
                return True
        return False

    @staticmethod
    def from_doc(doc):
        return Recipe(
            id=doc['id'],
            title=doc['title'],
            src=doc['src'],
            dst=doc['dst'],
            domain=doc['domain'],
            author=doc.get('author'),
            author_url=doc.get('author_url'),
            image_src=doc.get('image_src'),
            ingredients=[
                RecipeIngredient.from_doc(ingredient)
                for ingredient in doc['ingredients']
                if ingredient['description'].strip()
            ],
            directions=[
                RecipeDirection.from_doc(direction)
                for direction in doc.get('directions') or []
                if direction['description'].strip()
            ],
            servings=doc['servings'],
            time=doc['time'],
            rating=doc['rating'],
            nutrition=IngredientNutrition.from_doc(doc['nutrition'])
            if doc.get('nutrition') else None
        )

    def to_dict(self, include=None):
        return {
            'id': self.id,
            'title': self.title,
            'time': self.time,
            'ingredients': [
                ingredient.to_dict(include)
                for ingredient in self.ingredients
            ],
            'directions': [
                direction.to_dict()
                for direction in sorted(self.directions, key=lambda x: x.index)
            ],
            'servings': self.servings,
            'rating': self.rating,
            'dst': self.dst,
            'domain': self.domain,
            'author': self.author,
            'author_url': self.author_url,
            'image_url': self.image_path,
            'nutrition': self.nutrition.to_dict() if self.nutrition else None,
        }

    @property
    def image_path(self):
        return f'images/recipes/{self.id}.png'

    @property
    def contents(self):
        contents = set()
        for product in self.products:
            contents |= set(product.contents or [])
        return list(contents)
