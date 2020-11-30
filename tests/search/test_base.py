from reciperadar.search.base import EntityClause


def test_entity_clause_parsing():
    args = ['tomato', '-garlic', 'olives']
    clauses = EntityClause.from_args(args)

    expected_results = [
        ('tomato', True),
        ('garlic', False),
        ('olives', True),
    ]
    actual_results = [
        (clause.term, clause.positive)
        for clause in clauses
    ]

    assert expected_results == actual_results
