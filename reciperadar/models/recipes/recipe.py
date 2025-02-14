from reciperadar import db
from reciperadar.models.base import Searchable, Storable
from reciperadar.models.recipes.ingredient import RecipeIngredient
from reciperadar.models.recipes.nutrition import RecipeNutrition


class Recipe(Storable, Searchable):
    __tablename__ = "recipes"

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    src = db.Column(db.String)
    dst = db.Column(db.String)
    domain = db.Column(db.String)
    author = db.Column(db.String)
    author_url = db.Column(db.String)
    time = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    rating = db.Column(db.Float)
    nutrition = db.Column(db.JSON)
    nutrition_source = db.Column(db.String)
    ingredients = db.relationship("RecipeIngredient", passive_deletes="all")
    nutrition = db.relationship("RecipeNutrition", uselist=False, passive_deletes="all")
    is_dairy_free = db.Column(db.Boolean)
    is_gluten_free = db.Column(db.Boolean)
    is_vegan = db.Column(db.Boolean)
    is_vegetarian = db.Column(db.Boolean)

    indexed_at = db.Column(db.DateTime)

    redirected_id = db.Column(db.String)
    redirected_at = db.Column(db.DateTime)

    @property
    def noun(self):
        return "recipes"

    @property
    def url(self):
        return f"/#action=view&id={self.id}"

    @property
    def products(self):
        unique_products = {
            ingredient.product.singular: ingredient.product
            for ingredient in self.ingredients
        }
        return unique_products.values()

    @property
    def hidden(self):
        for ingredient in self.ingredients:
            if not ingredient.product.singular:
                return True
        return False

    @staticmethod
    def from_doc(doc):
        return Recipe(
            id=doc["id"],
            title=doc["title"],
            src=doc["src"],
            dst=doc["dst"],
            domain=doc["domain"],
            author=doc.get("author"),
            author_url=doc.get("author_url"),
            ingredients=[
                RecipeIngredient.from_doc(ingredient)
                for ingredient in doc["ingredients"]
                if ingredient["description"].strip()
            ],
            nutrition=(
                RecipeNutrition.from_doc(doc["nutrition"])
                if doc.get("nutrition")
                else None
            ),
            nutrition_source=doc.get("nutrition_source"),
            is_dairy_free=doc.get("is_dairy_free"),
            is_gluten_free=doc.get("is_gluten_free"),
            is_vegan=doc.get("is_vegan"),
            is_vegetarian=doc.get("is_vegetarian"),
            servings=doc["servings"],
            time=doc["time"],
            rating=doc["rating"],
            indexed_at=doc["indexed_at"],
            redirected_id=doc.get("redirected_id"),
            redirected_at=doc.get("redirected_at"),
        )

    def to_dict(self, ingredients=None):
        return {
            "id": self.id,
            "title": self.title,
            "time": self.time,
            "ingredients": [
                ingredient.to_dict(ingredients) for ingredient in self.ingredients
            ],
            "directions": [
                # direction.to_dict()
                # for direction
                # in sorted(self.directions, key=lambda x: x.index)
            ],
            "servings": self.servings,
            "rating": self.rating,
            "dst": self.dst,
            "domain": self.domain,
            "author": self.author,
            "author_url": self.author_url,
            "nutrition": (
                self.nutrition.to_dict()
                if self.nutrition and self.nutrition_source == "crawler"
                else None
            ),
            "is_dairy_free": self.is_dairy_free,
            "is_gluten_free": self.is_gluten_free,
            "is_vegan": self.is_vegan,
            "is_vegetarian": self.is_vegetarian,
        }
