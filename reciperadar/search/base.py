from abc import ABC

from opensearchpy import OpenSearch


class EntityClause:
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
    def term_list(clauses, condition=lambda x: True, synonyms=None):
        synonyms = synonyms or {}
        seen = set()
        terms = []
        for clause in filter(condition, clauses):
            for expansion in synonyms.get(clause.term) or [clause.term]:
                if expansion in seen:
                    continue
                seen.add(expansion)
                terms.append(expansion)
        return terms


class QueryRepository:
    __metaclass__ = ABC

    es = OpenSearch("opensearch")
