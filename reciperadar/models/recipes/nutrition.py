from reciperadar import db
from reciperadar.models.base import Storable


class IngredientNutrition(Storable):
    __tablename__ = 'ingredient_nutrition'

    fk = db.ForeignKey('recipe_ingredients.id', ondelete='cascade')
    ingredient_id = db.Column(db.String, fk, index=True)

    id = db.Column(db.String, primary_key=True)
    carbohydrates = db.Column(db.Float)
    energy = db.Column(db.Float)
    fat = db.Column(db.Float)
    fibre = db.Column(db.Float)
    protein = db.Column(db.Float)

    @staticmethod
    def from_doc(doc):
        nutrition_id = doc.get('id') or IngredientNutrition.generate_id()
        return IngredientNutrition(
            id=nutrition_id,
            carbohydrates=doc.get('carbohydrates'),
            energy=doc.get('energy'),
            fat=doc.get('fat'),
            fibre=doc.get('fibre'),
            protein=doc.get('protein'),
        )

    def to_dict(self):
        return {
            'carbohydrates': {
                'magnitude': self.carbohydrates,
                'units': 'g',
            },
            'energy': {
                'magnitude': self.energy,
                'units': 'cal',
            },
            'fat': {
                'magnitude': self.fat,
                'units': 'g',
            },
            'fibre': {
                'magnitude': self.fibre,
                'units': 'g',
            },
            'protein': {
                'magnitude': self.protein,
                'units': 'g',
            },
        }
