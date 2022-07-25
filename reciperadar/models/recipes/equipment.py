from reciperadar.models.base import Storable


class DirectionEquipment(Storable):
    __abstract__ = True

    @staticmethod
    def from_doc(doc):
        from reciperadar.models.recipes.appliance import DirectionAppliance
        from reciperadar.models.recipes.utensil import DirectionUtensil
        from reciperadar.models.recipes.vessel import DirectionVessel

        return {
            "appliance": DirectionAppliance,
            "utensil": DirectionUtensil,
            "vessel": DirectionVessel,
        }[doc["category"]].from_doc(doc)
