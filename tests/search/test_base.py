from reciperadar.search.base import EntityClause


def test_entity_clause_parsing():
    args = ["tomato", "-garlic", "olives"]
    clauses = EntityClause.from_args(args)

    expected_results = [
        ("tomato", True),
        ("garlic", False),
        ("olives", True),
    ]
    actual_results = [(clause.term, clause.positive) for clause in clauses]

    assert expected_results == actual_results


def test_entity_clause_term_list_expansion():
    args = ["coriander", "basil"]
    clauses = EntityClause.from_args(args)
    synonyms = {"coriander": ["cilantro", "coriander"]}

    expected_results = ["basil", "cilantro", "coriander"]
    actual_results = EntityClause.term_list(clauses, synonyms=synonyms)

    assert set(expected_results) == set(actual_results)


def test_entity_clause_term_list_preserve_ordering():
    args = ["cilantro", "basil"]
    clauses = EntityClause.from_args(args)
    synonyms = {"cilantro": ["cilantro", "coriander"]}

    expected_results = ["cilantro", "coriander", "basil"]
    actual_results = EntityClause.term_list(clauses, synonyms=synonyms)

    assert expected_results == actual_results
