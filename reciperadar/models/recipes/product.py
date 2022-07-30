from sqlalchemy.dialects import postgresql

from reciperadar import db
from reciperadar.models.base import Storable
from reciperadar.search.base import EntityClause


class Product(Storable):
    __tablename__ = "ingredient_products"

    ingredient_fk = db.ForeignKey("recipe_ingredients.id")
    ingredient_id = db.Column(db.String, ingredient_fk)

    id = db.Column(db.String, primary_key=True)
    product_parser = db.Column(db.String)
    singular = db.Column(db.String)
    plural = db.Column(db.String)
    category = db.Column(db.String)
    contents = db.Column(postgresql.ARRAY(db.String))

    STATE_AVAILABLE = "available"
    STATE_REQUIRED = "required"

    @staticmethod
    def from_doc(doc):
        return Product(
            id=doc.get("id"),
            product_parser=doc.get("product_parser"),
            singular=doc.get("singular"),
            plural=doc.get("plural"),
            category=doc.get("category"),
            contents=doc.get("contents"),
        )

    def state(self, ingredients):
        ingredients = ingredients or []
        states = {
            True: Product.STATE_AVAILABLE,
            False: Product.STATE_REQUIRED,
        }
        include = EntityClause.term_list(ingredients, lambda x: x.positive)
        available = bool(set(self.contents or []) & set(include))
        return states[available]

    def to_dict(self, ingredients):
        return {
            "id": self.id,
            "category": self.category,
            "singular": self.singular,
            "plural": self.plural,
            "state": self.state(ingredients),
        }
