from abc import ABC, abstractmethod, abstractproperty
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

from reciperadar import db


class Storable(db.Model):
    __abstract__ = True

    def to_dict(self):
        raise NotImplementedError(
            f"No response representation defined for {self.__class__.__name__}"
        )


class Searchable:
    __metaclass__ = ABC

    es = OpenSearch("opensearch")

    @abstractmethod
    def from_doc(doc):
        pass

    @abstractproperty
    def noun(self):
        pass

    def get_by_id(self, id):
        try:
            doc = self.es.get(index=self.noun, id=id)
        except NotFoundError:
            return None
        return self.from_doc(doc["_source"])
