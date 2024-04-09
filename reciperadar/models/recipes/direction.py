from reciperadar import db
from reciperadar.models.base import Storable
from reciperadar.models.recipes.equipment import DirectionEquipment
from reciperadar.models.recipes.appliance import DirectionAppliance
from reciperadar.models.recipes.utensil import DirectionUtensil
from reciperadar.models.recipes.vessel import DirectionVessel


class RecipeDirection(Storable):
    __tablename__ = "recipe_directions"

    fk = db.ForeignKey("recipes.id")
    recipe_id = db.Column(db.String, fk)

    id = db.Column(db.String, primary_key=True)
    index = db.Column(db.Integer)
    description = db.Column(db.String)
    markup = db.Column(db.String)
    appliances = db.relationship("DirectionAppliance", passive_deletes="all")
    utensils = db.relationship("DirectionUtensil", passive_deletes="all")
    vessels = db.relationship("DirectionVessel", passive_deletes="all")

    @staticmethod
    def from_doc(doc):
        equipment = [
            DirectionEquipment.from_doc(equipment) for equipment in doc["equipment"]
        ]
        return RecipeDirection(
            id=doc["id"],
            index=doc["index"],
            description=doc["description"],
            markup=doc["markup"],
            appliances=list(filter(lambda e: type(e) is DirectionAppliance, equipment)),
            utensils=list(filter(lambda e: type(e) is DirectionUtensil, equipment)),
            vessels=list(filter(lambda e: type(e) is DirectionVessel, equipment)),
        )

    def to_dict(self):
        return {
            "markup": self.markup,
        }
