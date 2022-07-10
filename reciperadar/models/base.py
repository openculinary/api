from abc import ABC, abstractmethod, abstractproperty
from basest.core import encode
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from uuid import uuid4

from reciperadar import db


class Storable(db.Model):
    __abstract__ = True

    ID_SYMBOL_TABLE = [
        s for s in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    ]

    @staticmethod
    def generate_id(input_bytes=None):
        return str().join(
            encode(
                input_data=input_bytes or uuid4().bytes,
                input_base=256,
                input_symbol_table=[b for b in range(256)],
                output_base=58,
                output_symbol_table=Storable.ID_SYMBOL_TABLE,
                output_padding="",
                input_ratio=16,
                output_ratio=22,
            )
        )

    def to_dict(self):
        raise NotImplementedError(
            f"No response representation defined for {self.__class__.__name__}"
        )


class Searchable(object):
    __metaclass__ = ABC

    es = Elasticsearch("elasticsearch")

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
