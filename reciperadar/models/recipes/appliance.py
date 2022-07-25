from reciperadar import db
from reciperadar.models.recipes.equipment import DirectionEquipment


class DirectionAppliance(DirectionEquipment):
    __tablename__ = "direction_appliances"

    fk = db.ForeignKey("recipe_directions.id")
    direction_id = db.Column(db.String, fk)

    id = db.Column(db.String, primary_key=True)
    appliance = db.Column(db.String)

    @staticmethod
    def from_doc(doc):
        return DirectionAppliance(
            id=doc["id"],
            appliance=doc["name"],
        )
