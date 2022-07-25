from reciperadar import db
from reciperadar.models.recipes.equipment import DirectionEquipment


class DirectionVessel(DirectionEquipment):
    __tablename__ = "direction_vessels"

    fk = db.ForeignKey("recipe_directions.id")
    direction_id = db.Column(db.String, fk)

    id = db.Column(db.String, primary_key=True)
    vessel = db.Column(db.String)

    @staticmethod
    def from_doc(doc):
        vessel_id = doc.get("id") or DirectionVessel.generate_id()
        return DirectionVessel(
            id=vessel_id,
            vessel=doc["name"],
        )
