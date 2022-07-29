from abc import ABC

from elasticsearch import Elasticsearch


class EntityClause(object):
    def __init__(self, term, positive):
        self.term = term
        self.positive = positive

    def __eq__(self, obj):
        return self.term == obj.term and self.positive == obj.positive

    @property
    def negative(self):
        return not self.positive

    @staticmethod
    def from_arg(arg):
        return EntityClause(arg.lstrip("-"), positive=not arg.startswith("-"))

    @staticmethod
    def from_args(args):
        return [EntityClause.from_arg(arg) for arg in args]

    @staticmethod
    def term_list(clauses, synonyms=None, condition=lambda x: True):
        synonyms = synonyms or {}
        terms = set()
        for clause in filter(condition, clauses):
            for expansion in synonyms.get(clause.term) or [clause.term]:
                terms.add(expansion)
        return list(terms)


class QueryRepository(object):
    __metaclass__ = ABC

    es = Elasticsearch("elasticsearch")
