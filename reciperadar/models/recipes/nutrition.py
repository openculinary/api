from reciperadar import db
from reciperadar.models.base import Storable


class Nutrition(Storable):
    __abstract__ = True

    id = db.Column(db.String, primary_key=True)
    carbohydrates = db.Column(db.Float)
    carbohydrates_units = db.Column(db.String)
    energy = db.Column(db.Float)
    energy_units = db.Column(db.String)
    fat = db.Column(db.Float)
    fat_units = db.Column(db.String)
    fibre = db.Column(db.Float)
    fibre_units = db.Column(db.String)
    protein = db.Column(db.Float)
    protein_units = db.Column(db.String)

    def to_dict(self):
        return {
            "carbohydrates": {
                "magnitude": self.carbohydrates,
                "units": self.carbohydrates_units,
            },
            "energy": {
                "magnitude": self.energy,
                "units": self.energy_units,
            },
            "fat": {
                "magnitude": self.fat,
                "units": self.fat_units,
            },
            "fibre": {
                "magnitude": self.fibre,
                "units": self.fibre_units,
            },
            "protein": {
                "magnitude": self.protein,
                "units": self.protein_units,
            },
        }


class RecipeNutrition(Nutrition):
    __tablename__ = "recipe_nutrition"

    fk = db.ForeignKey("recipes.id")
    recipe_id = db.Column(db.String, fk)

    @staticmethod
    def from_doc(doc):
        return RecipeNutrition(
            carbohydrates=doc.get("carbohydrates"),
            carbohydrates_units=doc.get("carbohydrates_units"),
            energy=doc.get("energy"),
            energy_units=doc.get("energy_units"),
            fat=doc.get("fat"),
            fat_units=doc.get("fat_units"),
            fibre=doc.get("fibre"),
            fibre_units=doc.get("fibre_units"),
            protein=doc.get("protein"),
            protein_units=doc.get("protein_units"),
        )
