from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
)

from reciperadar.models.base import Storable


class IngredientProduct(Storable):
    __tablename__ = 'ingredient_products'

    fk = ForeignKey('recipe_ingredients.id', ondelete='cascade')
    ingredient_id = Column(String, fk, index=True)

    id = Column(String, primary_key=True)
    product = Column(String)
    product_parser = Column(String)
    is_plural = Column(Boolean)
    singular = Column(String)
    plural = Column(String)

    STATE_AVAILABLE = 'available'
    STATE_REQUIRED = 'required'

    _category = None
    _contents = None

    @staticmethod
    def from_doc(doc):
        product = doc.get('product')
        is_plural = doc.get('is_plural')
        singular = doc.get('singular')
        plural = doc.get('plural')

        product_id = doc.get('id') or IngredientProduct.generate_id()
        return IngredientProduct(
            id=product_id,
            product=product,
            product_parser=doc.get('product_parser'),
            is_plural=is_plural,
            singular=singular,
            plural=plural,
            _category=doc.get('category'),
            _contents=doc.get('contents')
        )

    def to_doc(self):
        result = super().to_doc()
        result['category'] = self.category
        result['contents'] = self.contents
        return result

    def to_dict(self, include):
        states = {
            True: IngredientProduct.STATE_AVAILABLE,
            False: IngredientProduct.STATE_REQUIRED,
        }
        available = bool(set(self.contents) & set(include or []))

        return {
            'type': 'product',
            'value': self.product,
            'category': self.category,
            'singular': self.singular,
            'plural': self.plural,
            'state': states[available]
        }
