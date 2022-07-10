from abc import ABC

from elasticsearch import Elasticsearch


class EntityClause(object):
    def __init__(self, term, positive):
        self.term = term
        self.positive = positive

    @staticmethod
    def from_arg(arg):
        return EntityClause(arg.lstrip("-"), positive=not arg.startswith("-"))

    @staticmethod
    def from_args(args):
        return [EntityClause.from_arg(arg) for arg in args]

    @staticmethod
    def term_list(clauses, condition=lambda x: True):
        return list(set(map(lambda x: x.term, filter(condition, clauses))))


class QueryRepository(object):
    __metaclass__ = ABC

    es = Elasticsearch("elasticsearch")
