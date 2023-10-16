from reciperadar.search.base import QueryRepository


class EquipmentSearch(QueryRepository):
    def autosuggest(self, prefix):
        prefix = prefix.lower()
        query = {
            "aggregations": {
                "equipment": {
                    "filter": {
                        "bool": {
                            "should": [
                                {"match": {"equipment_names": prefix}},
                                {"prefix": {"equipment_names": prefix}},
                            ]
                        }
                    },
                    "aggregations": {
                        "equipment": {
                            "terms": {
                                "field": "equipment_names",
                                "include": f"{prefix}.*",
                                "min_doc_count": 1,
                                "size": 10,
                            }
                        }
                    },
                }
            }
        }
        results = self.es.search(index="recipes", body=query)["aggregations"]
        results = results["equipment"]["equipment"]["buckets"]

        results.sort(
            key=lambda s: (
                s["key"] != prefix,  # exact matches first
                not s["key"].startswith(prefix),  # prefix matches next
                len(s["key"]),
            ),  # sort remaining matches by length
        )
        return [{"equipment": result["key"]} for result in results]
