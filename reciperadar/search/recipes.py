from collections import defaultdict
from datetime import UTC, datetime, timedelta

from reciperadar import app
from reciperadar.models.recipes import Recipe
from reciperadar.search.base import EntityClause, QueryRepository
from reciperadar.search.ingredients import IngredientSearch


def load_ingredient_synonyms():
    # Return cached synonyms if they are available and have not yet expired
    if hasattr(app, "ingredient_synonyms"):
        expiry = app.ingredient_synonyms_loaded_at + timedelta(hours=1)
        if datetime.now(tz=UTC) < expiry:
            return app.ingredient_synonyms

    # Otherwise, attempt to update the synonym cache
    synonyms = IngredientSearch().synonyms()
    if synonyms:
        app.ingredient_synonyms = synonyms
        app.ingredient_synonyms_loaded_at = datetime.now(tz=UTC)

    # Return the latest-known synonyms
    if hasattr(app, "ingredient_synonyms"):
        return app.ingredient_synonyms


class RecipeSearch(QueryRepository):
    @staticmethod
    def _generate_include_clause(ingredients):
        synonyms = load_ingredient_synonyms()
        include = EntityClause.term_list(ingredients, lambda x: x.positive, synonyms)
        return [
            {
                "constant_score": {
                    "boost": pow(10, idx),
                    "filter": {"match": {"contents": inc}},
                }
            }
            for idx, inc in enumerate(reversed(include))
        ]

    @staticmethod
    def _generate_include_exact_clause(ingredients):
        synonyms = load_ingredient_synonyms()
        include = EntityClause.term_list(ingredients, lambda x: x.positive, synonyms)
        return [
            {
                "nested": {
                    "path": "ingredients",
                    "query": {
                        "constant_score": {
                            "boost": pow(10, idx) * 2,
                            "filter": {"match": {"ingredients.product.singular": inc}},
                        }
                    },
                }
            }
            for idx, inc in enumerate(reversed(include))
        ]

    @staticmethod
    def _generate_exclude_clause(ingredients):
        synonyms = load_ingredient_synonyms()
        exclude = EntityClause.term_list(ingredients, lambda x: x.negative, synonyms)
        return [
            # exclude 'hidden' recipes
            {"match": {"hidden": True}},
        ] + [
            # match any ingredients in the exclude list
            {"match": {"contents": exc}}
            for exc in exclude
        ]

    @staticmethod
    def sort_methods(match_count=1):
        score_limit = pow(10, match_count) * 2
        preamble = f"""
            def product_count = doc.product_count.value;
            def exact_found_count = 0;
            def found_count = 0;
            for (def score = (long) _score; score > 0; score /= 10) {{
                if (score % 10 > 2) exact_found_count++;
                if (score % 10 > 0) found_count++;
            }}
            def missing_count = product_count - found_count;
            def exact_missing_count = product_count - exact_found_count;

            def relevance_score = (found_count * 2 + exact_found_count);
            def normalized_score = _score / {float(score_limit)};
            def missing_score = (exact_missing_count * 2 - missing_count);
            def missing_ratio = missing_count / product_count;
        """
        return {
            # rank: number of ingredient matches
            # tiebreak: normalized relevance score
            "relevance": {
                "script": f"{preamble} relevance_score + normalized_score",
                "order": "desc",
            },
            # rank: number of missing ingredients
            # tiebreak: normalized relevance score
            "ingredients": {
                "script": f"{preamble} missing_score + 1 - normalized_score",
                "order": "asc",
            },
            # rank: preparation time
            # tiebreak: percentage of missing ingredients
            "duration": {
                "script": f"{preamble} doc.time.value + missing_ratio",
                "order": "asc",
            },
        }

    def _generate_sort_method(self, ingredients, sort):
        # set the default sort method
        if not sort:
            sort = "relevance"
        # if no ingredients are specified, we may be able to short-cut sorting
        include = [True for x in ingredients if x.positive]
        if include == [] and sort != "duration":
            return {"script": "doc.rating.value", "order": "desc"}
        return self.sort_methods(match_count=len(include))[sort]

    def _domain_facets(self):
        return {"domains": {"terms": {"field": "domain", "size": 100}}}

    def _product_filter(self, ingredients, dietary_properties):
        conditions = defaultdict(list)

        # Do not present staple ingredients as choices
        match = {"term": {"ingredients.product.is_kitchen_staple": True}}
        conditions["must_not"].append(match)

        # Do not present already-selected ingredients as choices
        for ingredient in ingredients:
            match = {"term": {"ingredients.product.singular": ingredient.term}}
            conditions["must_not"].append(match)

        # Filter to products that satisfy the user's dietary requirements
        for dietary_property in dietary_properties:
            field = f"ingredients.product.{dietary_property.term}"
            match = {"term": {field: True}}
            conditions["filter"].append(match)

        return {"bool": conditions}

    def _product_aggregation(self):
        return {
            "singular": {
                "terms": {
                    "field": "ingredients.product.singular",
                    "order": {"_count": "desc"},
                    "size": 50,
                }
            }
        }

    def _product_suggestions(self, ingredients, dietary_properties):
        product_filter = self._product_filter(ingredients, dietary_properties)
        product_aggregation = self._product_aggregation()
        return {
            "products": {
                "nested": {"path": "ingredients"},
                "aggs": {
                    "choices": {
                        "filter": product_filter,
                        "aggs": product_aggregation,
                    }
                },
            }
        }

    def _generate_aggregations(self, suggest_products, ingredients, dietary_properties):
        aggregations = {
            **self._domain_facets(),
            **(
                self._product_suggestions(ingredients, dietary_properties)
                if suggest_products
                else {}
            ),
        }
        return {
            "prefilter": {
                "filter": {"match_all": {}},
                "aggs": aggregations,
            }
        }

    def _generate_post_filter(self, domains):
        conditions = defaultdict(list)
        for domain in domains:
            condition = "filter" if domain.positive else "must_not"
            match = {"match": {"domain": domain.term}}
            conditions[condition].append(match)
        return {"bool": conditions}

    def _render_query(
        self,
        ingredients,
        dietary_properties,
        sort,
        exact_match=True,
        min_include_match=None,
    ):
        include_exact_clause = self._generate_include_exact_clause(ingredients)
        include_clause = self._generate_include_clause(ingredients)
        exclude_clause = self._generate_exclude_clause(ingredients)
        sort_params = self._generate_sort_method(ingredients, sort)

        should = include_exact_clause if exact_match else include_clause
        must_not = exclude_clause
        filter = [
            {"range": {"time": {"gte": 5}}},
            {"range": {"product_count": {"gt": 0}}},
        ]
        for dietary_property in dietary_properties:
            match = {"match": {dietary_property.term: True}}
            filter.append(match)
        if min_include_match is None:
            min_include_match = len(should)

        return {
            "function_score": {
                "boost_mode": "replace",
                "query": {
                    "bool": {
                        "should": should,
                        "must_not": must_not,
                        "filter": filter,
                        "minimum_should_match": min_include_match,
                    }
                },
                "script_score": {"script": {"source": sort_params["script"]}},
            }
        }, [{"_score": sort_params["order"]}]

    def _refined_queries(self, ingredients, dietary_properties, sort):
        # Provide an 'empty query' hint
        if not any([ingredients, sort]):
            query, sort_method = self._render_query(
                ingredients=ingredients,
                dietary_properties=dietary_properties,
                sort=sort,
            )
            yield query, sort_method, "empty_query"
            return

        for exact_match in [False]:
            query, sort_method = self._render_query(
                ingredients=ingredients,
                dietary_properties=dietary_properties,
                exact_match=exact_match,
                sort=sort,
            )
            yield query, sort_method, None

        positive_ingredients = sum(x.positive for x in ingredients)
        if positive_ingredients > 1:
            for min_include_match in range(positive_ingredients - 1, 0, -1):
                for exact_match in [False]:
                    query, sort_method = self._render_query(
                        ingredients=ingredients,
                        dietary_properties=dietary_properties,
                        sort=sort,
                        exact_match=exact_match,
                        min_include_match=min_include_match,
                    )
                    yield query, sort_method, "match_any"

    def query(
        self,
        ingredients,
        equipment,
        offset,
        limit,
        sort,
        domains,
        dietary_properties,
        allow_refinement=True,
        suggest_products=False,
    ):
        """
        Searching for recipes is currently supported in three different modes:

        * 'relevance' mode prioritizes matching as many ingredients as possible
        * 'ingredients' mode aims to find recipes with fewest extras required
        * 'duration' mode finds recipes that can be prepared most quickly

        In the search index, each recipe contains a list of ingredients.
        Each ingredient is identified by the 'ingredient.product.singular'
        field.

        When users select auto-suggested ingredients, they may be choosing from
        either singular or plural names - i.e. 'potato' or 'potatoes' may
        appear in their user interface.

        When the client makes a search request, it should always use the
        singular ingredient name form - 'potato' in the example above.  This
        allows the search engine to match against the corresponding singular
        ingredient name in the recipe index.

        Recipe index

                            Ingredient text         Indexed ingredient name
        recipe 1            "3 sweet potatoes"  ->  "sweet potato"
                            "1 onion"           ->  "onion"
                            ...
        recipe 2            "2kg onions"        ->  "onion"
                            ...


        End-to-end search

        Autosuggest     Client query    Recipe matches  Displayed to user
        ["onions"]  ->  ["onion"]   ->  recipe 1   ->   "3 sweet potatoes"
                                                        "1 onion"
                                                        ...
                                        recipe 2   ->   "2kg onions"
                                                        ...


        Recipes also contain an aggregated 'contents' field, which contains all
        of the ingredient identifiers and also their related ingredient names.

        Related ingredients can include ingredient ancestors (i.e. 'tortilla'
        is an ancestor of 'flour tortilla').

        Example:
        {
          'title': 'Tofu stir-fry',
          'ingredients': [
            {
              'product': {
                'singular': 'firm tofu',
                ...
              }
            },
            ...
          ],
          'contents': [
            'firm tofu',
            'tofu',
            ...
          ]
        }

        Some queries are quite straightforward under this model.

        A search for 'firm tofu' can simply match on any recipes with 'firm
        tofu' in the 'contents' field.

        A more complex example is a search for 'tofu', where we want recipes
        which contain either 'tofu' or 'firm tofu' to appear.  In this
        situation, we would prefer exact-matches on 'tofu' to appear before
        matches on 'firm tofu' which are a less precise match for the query.

        In this case we can search on the 'contents' field and we will find the
        recipe, but in order to determine whether a recipe contained an 'exact'
        match we also need to check the 'ingredient.product.singular' field and
        record whether the query term was present.

        To achieve this, we use OpenSearch's query syntax to encode information
        about the quality of each match during search execution.

        We use `constant_score` queries to store a power-of-ten score for each
        query ingredient, with the value doubled for exact matches.

        For example, in a query for `onion`, `tomato`, `tofu`:

                                onion   tomato  tofu        score
        recipe 1                exact   exact   partial     300 + 30 + 1 = 331
        recipe 2                partial no      exact       100 +  0 + 3 = 103
        recipe 3                exact   no      exact       300 +  0 + 3 = 303

        This allows the final sorting stage to determine - with some small
        possibility of error* - how many exact and inexact matches were
        discovered for each recipe.

                                score   exact_matches       all_matches
        recipe 1                331     1 + 1 + 0 = 2       1 + 1 + 1 = 3
        recipe 2                103     0 + 0 + 1 = 1       1 + 0 + 1 = 2
        recipe 3                303     1 + 0 + 1 = 2       1 + 0 + 1 = 2

        At this stage we have enough information to sort the result set based
        on the number of overall matches and to use the number of exact matches
        as a tiebreaker within each group.

        Result ranking:

        - (3 matches, 2 exact) recipe 1
        - (2 matches, 2 exact) recipe 3
        - (2 matches, 1 exact) recipe 2


        * Inconsistent results and ranking errors can occur if an ingredient
          appears multiple times in a recipe, resulting in duplicate counts
        """
        offset = max(0, offset)
        limit = max(0, limit)
        limit = min(25, limit)

        aggregations = self._generate_aggregations(
            suggest_products=suggest_products,
            ingredients=ingredients,
            dietary_properties=dietary_properties,
        )
        post_filter = self._generate_post_filter(domains=domains)

        queries = self._refined_queries(
            ingredients=ingredients,
            dietary_properties=dietary_properties,
            sort=sort,
        )
        for query, sort_method, refinement in queries:
            results = self.es.search(
                index="recipes",
                body={
                    "query": query,
                    "from": offset,
                    "size": limit,
                    "sort": sort_method,
                    "aggs": aggregations,
                    "post_filter": post_filter,
                },
            )
            if not allow_refinement:
                break
            if results["aggregations"]["prefilter"]["doc_count"] >= 5:
                break

        recipes = []
        for result in results["hits"]["hits"]:
            recipe = Recipe.from_doc(result["_source"])
            recipes.append(recipe.to_dict(ingredients))

        # TODO: Can this bucket sorting be moved into the aggregation pipeline?
        if suggest_products:
            prefilter = results["aggregations"]["prefilter"]
            total = prefilter["doc_count"]

            products = prefilter["products"]["choices"]["singular"]["buckets"]
            products = [x for x in products if x["doc_count"] != total]
            products.sort(key=lambda x: abs(x["doc_count"] - (total / 2)))
            prefilter["products"] = {"buckets": products[:10]}

        facets = {}
        for field, content in results["aggregations"]["prefilter"].items():
            if not isinstance(content, dict) or "buckets" not in content:
                continue
            facets[field] = [
                {
                    "key": bucket["key"],
                    "count": min(bucket["doc_count"], 100),
                }
                for bucket in content["buckets"]
            ]

        refinements = [refinement] if recipes and refinement else []
        if equipment:
            refinements += ["equipment_search_unavailable"]

        return {
            "authority": "api",
            "total": min(results["hits"]["total"]["value"], 25 * limit),
            "results": recipes,
            "facets": facets,
            "refinements": refinements,
        }

    def explore(self, ingredients, dietary_properties):
        depth = len(ingredients)
        limit = 10 if depth >= 3 else 0
        return self.query(
            ingredients=ingredients,
            equipment=[],
            offset=0,
            limit=limit,
            sort=None,
            domains=[],
            dietary_properties=dietary_properties,
            allow_refinement=False,
            suggest_products=True,
        )
