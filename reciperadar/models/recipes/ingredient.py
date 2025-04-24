from reciperadar import db
from reciperadar.models.base import Storable
from reciperadar.models.recipes.product import Product


class RecipeIngredient(Storable):
    __tablename__ = "recipe_ingredients"

    recipe_fk = db.ForeignKey("recipes.id")
    recipe_id = db.Column(db.String, recipe_fk)

    product_fk = db.ForeignKey("products.id")
    product_id = db.Column(db.String, product_fk)

    id = db.Column(db.String, primary_key=True)
    index = db.Column(db.Integer)
    description = db.Column(db.String)
    markup = db.Column(db.String)

    product = db.relationship("Product", uselist=False)

    magnitude = db.Column(db.Float)
    magnitude_parser = db.Column(db.String)
    units = db.Column(db.String)
    units_parser = db.Column(db.String)
    product_is_plural = db.Column(db.Boolean)
    product_parser = db.Column(db.String)
    verb = db.Column(db.String)

    @property
    def product_name(self):
        if self.product_is_plural:
            return self.product.plural
        else:
            return self.product.singular

    @staticmethod
    def from_doc(doc):
        return RecipeIngredient(
            id=doc["id"],
            index=doc["index"],
            description=doc["description"].strip(),
            markup=doc.get("markup"),
            product=Product.from_doc(doc["product"]),
            product_id=doc["product"].get("id"),
            product_is_plural=doc.get("product_is_plural"),
            product_parser=doc["product"].get("product_parser"),
            magnitude=doc.get("magnitude"),
            magnitude_parser=doc.get("magnitude_parser"),
            units=doc.get("units"),
            units_parser=doc.get("units_parser"),
            verb=doc.get("verb"),
        )

    def to_dict(self, ingredients=None):
        return {
            "markup": self.markup,
            "product": {
                **self.product.to_dict(ingredients),
                **{"name": self.product_name},
            },
            "quantity": {
                "magnitude": self.magnitude,
                "units": self.units,
            },
        }
