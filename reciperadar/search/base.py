from abc import ABC

from elasticsearch import Elasticsearch


class EntityClause(object):

    def __init__(self, term, positive):
        self.term = term
        self.positive = positive

    @staticmethod
    def from_arg(arg):
        positive = not arg.startswith('-')
        term = arg.lstrip('-')
        return EntityClause(term, positive)

    @staticmethod
    def from_args(args):
        return [EntityClause.from_arg(arg) for arg in args]

    @staticmethod
    def term_list(clauses, condition=lambda x: True):
        terms = set()
        for clause in filter(condition, clauses):
            terms.add(clause.term)
        return list(terms)


class QueryRepository(object):
    __metaclass__ = ABC

    es = Elasticsearch('elasticsearch')
