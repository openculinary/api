from reciperadar import db
from reciperadar.models.recipes.equipment import DirectionEquipment


class DirectionUtensil(DirectionEquipment):
    __tablename__ = "direction_utensils"

    fk = db.ForeignKey("recipe_directions.id")
    direction_id = db.Column(db.String, fk)

    id = db.Column(db.String, primary_key=True)
    utensil = db.Column(db.String)

    @staticmethod
    def from_doc(doc):
        return DirectionUtensil(
            id=doc["id"],
            utensil=doc["name"],
        )
