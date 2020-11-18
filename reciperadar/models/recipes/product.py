from sqlalchemy.dialects import postgresql

from reciperadar import db
from reciperadar.models.base import Storable


class Product(Storable):
    __tablename__ = 'ingredient_products'

    fk = db.ForeignKey('recipe_ingredients.id', ondelete='cascade')
    ingredient_id = db.Column(db.String, fk, index=True)

    id = db.Column(db.String, primary_key=True)
    product = db.Column(db.String)
    product_parser = db.Column(db.String)
    is_plural = db.Column(db.Boolean)
    singular = db.Column(db.String)
    plural = db.Column(db.String)
    category = db.Column(db.String)
    contents = db.Column(postgresql.ARRAY(db.String))

    STATE_AVAILABLE = 'available'
    STATE_REQUIRED = 'required'

    @staticmethod
    def from_doc(doc):
        plural = doc.get('plural')
        singular = doc.get('singular')
        is_plural = doc.get('is_plural')
        product = plural if is_plural else singular
        return Product(
            id=doc.get('id'),
            product=product,
            product_parser=doc.get('product_parser'),
            is_plural=is_plural,
            singular=singular,
            plural=plural,
            category=doc.get('category'),
            contents=doc.get('contents'),
        )

    def state(self, include):
        states = {
            True: Product.STATE_AVAILABLE,
            False: Product.STATE_REQUIRED,
        }
        available = bool(set(self.contents or []) & set(include or []))
        return states[available]

    def to_dict(self, include):
        return {
            'product_id': self.id,
            'product': self.product,
            'category': self.category,
            'singular': self.singular,
            'plural': self.plural,
            'state': self.state(include),
        }
