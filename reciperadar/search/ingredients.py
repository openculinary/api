from reciperadar.models.recipes.product import Product
from reciperadar.search.base import QueryRepository


class IngredientSearch(QueryRepository):
    def autosuggest(self, prefix):
        prefix = prefix.lower()
        query = {
            "aggregations": {
                # aggregate across all nested ingredient documents
                "ingredients": {
                    "nested": {"path": "ingredients"},
                    "aggregations": {
                        # filter to product names which match the user search
                        "products": {
                            "filter": {
                                "bool": {
                                    "should": [
                                        {
                                            "match": {
                                                "ingredients.product_name.autocomplete": {  # noqa
                                                    "query": prefix,
                                                    "operator": "AND",
                                                    "fuzziness": "AUTO",
                                                }
                                            }
                                        },
                                        {
                                            "prefix": {
                                                "ingredients.product_name": prefix
                                            }
                                        },
                                    ]
                                }
                            },
                            "aggregations": {
                                # retrieve the top products in singular pluralization
                                "product_id": {
                                    "terms": {
                                        "field": "ingredients.product.id",
                                        "min_doc_count": 5,
                                        "size": 10,
                                    },
                                    "aggregations": {
                                        # count products that were plural in the source recipe  # noqa
                                        "plurality": {
                                            "filter": {
                                                "match": {
                                                    "ingredients.product_is_plural": True  # noqa
                                                }
                                            }
                                        },
                                        # retrieve a category for each ingredient
                                        "category": {
                                            "terms": {
                                                "field": "ingredients.product.category",
                                                "size": 1,
                                            }
                                        },
                                        "singular": {
                                            "terms": {
                                                "field": "ingredients.product.singular",
                                                "size": 1,
                                            }
                                        },
                                        "plural": {
                                            "terms": {
                                                "field": "ingredients.product.plural",
                                                "size": 1,
                                            }
                                        },
                                    },
                                }
                            },
                        }
                    },
                }
            }
        }
        results = self.es.search(index="recipes", body=query)["aggregations"]
        results = results["ingredients"]["products"]["product_id"]["buckets"]

        # iterate through the suggestions and determine whether to display
        # the singular or plural form of the word based on how frequently
        # each form is used in the overall recipe corpus
        suggestions = []
        for result in results:
            total_count = result["doc_count"]
            plural_count = result["plurality"]["doc_count"]
            plural_wins = plural_count > total_count - plural_count

            product_id = result["key"]
            category = (result["category"]["buckets"] or [{}])[0].get("key")
            singular = (result["singular"]["buckets"] or [{}])[0].get("key")
            plural = (result["plural"]["buckets"] or [{}])[0].get("key")

            product = Product(
                id=product_id,
                category=category,
                singular=singular,
                plural=plural,
            )
            product.name = plural if plural_wins else singular
            suggestions.append(product)

        suggestions.sort(
            key=lambda s: (
                s.name != prefix,  # exact matches first
                not s.name.startswith(prefix),  # prefix matches next
                len(s.name),
            ),  # sort remaining matches by length
        )
        return [
            {
                "id": suggestion.id,
                "name": suggestion.name,
                "category": suggestion.category,
                "singular": suggestion.singular,
                "plural": suggestion.plural,
            }
            for suggestion in suggestions
        ]

    def synonyms(self):
        try:
            results = self.es.search(index="product_synonyms", size=10000)
        except Exception:
            return None
        return {
            result["_id"]: result["_source"]["synonyms"]
            for result in results["hits"]["hits"]
        }
