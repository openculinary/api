from reciperadar import db
from reciperadar.models.base import Storable
from reciperadar.models.recipes.nutrition import IngredientNutrition
from reciperadar.models.recipes.product import Product


class RecipeIngredient(Storable):
    __tablename__ = 'recipe_ingredients'

    recipe_fk = db.ForeignKey('recipes.id', ondelete='cascade')
    recipe_id = db.Column(db.String, recipe_fk, index=True)

    product_fk = db.ForeignKey('products.id', deferrable=True)
    product_id = db.Column(db.String, product_fk, index=True)

    id = db.Column(db.String, primary_key=True)
    index = db.Column(db.Integer)
    description = db.Column(db.String)
    markup = db.Column(db.String)

    product = db.relationship(
        'Product',
        uselist=False
    )
    nutrition = db.relationship(
        'IngredientNutrition',
        uselist=False,
        passive_deletes='all'
    )

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
        ingredient_id = doc.get('id') or RecipeIngredient.generate_id()
        nutrition = doc.get('nutrition')
        return RecipeIngredient(
            id=ingredient_id,
            index=doc['index'],
            description=doc['description'].strip(),
            markup=doc.get('markup'),
            product=Product.from_doc(doc['product']),
            product_id=doc['product'].get('id'),
            product_is_plural=doc.get('product_is_plural'),
            product_parser=doc['product'].get('product_parser'),
            nutrition=IngredientNutrition.from_doc(nutrition)
            if nutrition else None,
            magnitude=doc.get('magnitude'),
            magnitude_parser=doc.get('magnitude_parser'),
            units=doc.get('units'),
            units_parser=doc.get('units_parser'),
            verb=doc.get('verb'),
        )

    def to_dict(self, ingredients=None):
        return {
            'markup': self.markup,
            'product': {
                **self.product.to_dict(ingredients),
                # TODO: would a 'countable' flag on products be preferable?
                **{'name': self.product_name},
                # TODO: these fields are provided for backwards-compatibility
                **{
                    'product_id': self.product.id,
                    'product': self.product_name,
                },
            },
            'quantity': {
                'magnitude': self.magnitude,
                'units': self.units,
            }
        }
