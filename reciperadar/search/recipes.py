from collections import defaultdict

from reciperadar.models.recipes import Recipe
from reciperadar.search.base import QueryRepository


class RecipeSearch(QueryRepository):

    @staticmethod
    def _generate_include_clause(include):
        return [{
            'constant_score': {
                'boost': pow(10, idx),
                'filter': {
                    'match': {'contents': inc}
                }
            }
        } for idx, inc in enumerate(reversed(include))]

    @staticmethod
    def _generate_include_exact_clause(include):
        return [{
            'nested': {
                'path': 'ingredients',
                'query': {
                    'constant_score': {
                        'boost': pow(10, idx) * 2,
                        'filter': {
                            'match': {'ingredients.product.singular': inc}
                        }
                    }
                }
            }
        } for idx, inc in enumerate(reversed(include))]

    @staticmethod
    def _generate_exclude_clause(exclude):
        return [
            # exclude 'hidden' recipes
            {'match': {'hidden': True}},
        ] + [
            # match any ingredients in the exclude list
            {'match': {'contents': exc}} for exc in exclude
        ]

    @staticmethod
    def _generate_equipment_clause(equipment):
        return [
            {'match': {'directions.equipment.equipment': item}}
            for item in equipment
        ]

    @staticmethod
    def sort_methods():
        preamble = '''
            def product_count = doc.product_count.value;
            def exact_found_count = 0;
            def found_count = 0;
            for (def score = (long) _score; score > 0; score /= 10) {
                if (score % 10 > 2) exact_found_count++;
                if (score % 10 > 0) found_count++;
            }
            def missing_count = product_count - found_count;
            def exact_missing_count = product_count - exact_found_count;

            def relevance_score = (found_count * 2 + exact_found_count);
            def normalized_rating = doc.rating.value / 10;
            def missing_score = (exact_missing_count * 2 - missing_count);
            def missing_ratio = missing_count / product_count;
        '''
        return {
            # rank: number of ingredient matches
            # tiebreak: recipe rating
            'relevance': {
                'script': f'{preamble} relevance_score + normalized_rating',
                'order': 'desc'
            },

            # rank: number of missing ingredients
            # tiebreak: recipe rating
            'ingredients': {
                'script': f'{preamble} missing_score + 1 - normalized_rating',
                'order': 'asc'
            },

            # rank: preparation time
            # tiebreak: percentage of missing ingredients
            'duration': {
                'script': f'{preamble} doc.time.value + missing_ratio',
                'order': 'asc'
            },
        }

    def _generate_sort_method(self, include, sort):
        # set the default sort method
        if not sort:
            sort = 'relevance'
        # if no ingredients are specified, we may be able to short-cut sorting
        if not include and sort != 'duration':
            return {'script': 'doc.rating.value', 'order': 'desc'}
        return self.sort_methods()[sort]

    def _domain_facets(self):
        return {
            'domains': {
                'terms': {'field': 'domain', 'size': 100}
            }
        }

    def _product_filter(self, include, dietary_properties):
        return {
            'bool': {
                'must': [
                    {'term': {f'ingredients.product.{dietary_property}': True}}
                    for dietary_property in [
                        f'is_{dietary_property.replace("-", "_")}'
                        for dietary_property in dietary_properties
                    ]
                ],
                'must_not': [
                    # Do not present staple ingredients as choices
                    {'term': {'ingredients.product.is_kitchen_staple': True}}
                ] + [
                    # Do not present already-selected ingredients as choices
                    {'term': {'ingredients.product.singular': inc}}
                    for inc in include
                ]
            }
        }

    def _product_aggregatation(self):
        return {
            'singular': {
                'terms': {
                    'field': 'ingredients.product.singular',
                    'order': {'_count': 'desc'},
                    'size': 50
                }
            }
        }

    def _product_suggestions(self, include, dietary_properties):
        product_filter = self._product_filter(include, dietary_properties)
        product_aggregation = self._product_aggregatation()
        return {
            'products': {
                'nested': {'path': 'ingredients'},
                'aggs': {
                    'choices': {
                        'filter': product_filter,
                        'aggs': product_aggregation,
                    }
                }
            }
        }

    def _generate_aggregations(self, suggest_products, include,
                               dietary_properties):
        aggregations = {
            **self._domain_facets(),
            **(
                self._product_suggestions(include, dietary_properties)
                if suggest_products else {}
            )
        }
        return {
            'prefilter': {
                'filter': {'match_all': {}},
                'aggs': aggregations,
            }
        }

    def _generate_post_filter(self, domains, dietary_properties):
        conditions = defaultdict(list)
        for domain in domains:
            clause = 'must' if domain.positive else 'must_not'
            conditions[clause] += {'match': {'domain': domain.term}}
        if dietary_properties:
            conditions['must'] += [
                {'match': {f'is_{dietary_property.replace("-", "_")}': True}}
                for dietary_property in dietary_properties
            ]
        return {'bool': conditions}

    def _render_query(self, include, exclude, equipment, sort,
                      exact_match=True, min_include_match=None):
        include_exact_clause = self._generate_include_exact_clause(include)
        include_clause = self._generate_include_clause(include)
        exclude_clause = self._generate_exclude_clause(exclude)
        equipment_clause = self._generate_equipment_clause(equipment)
        sort_params = self._generate_sort_method(include, sort)

        should = include_exact_clause if exact_match else include_clause
        must_not = exclude_clause
        filter = equipment_clause + [
            {'range': {'time': {'gte': 5}}},
            {'range': {'product_count': {'gt': 0}}},
        ]
        if min_include_match is None:
            min_include_match = len(should)

        return {
            'function_score': {
                'boost_mode': 'replace',
                'query': {
                    'bool': {
                        'should': should,
                        'must_not': must_not,
                        'filter': filter,
                        'minimum_should_match': min_include_match,
                    }
                },
                'script_score': {'script': {'source': sort_params['script']}}
            }
        }, [{'_score': sort_params['order']}]

    def _refined_queries(self, include, exclude, equipment, sort):
        # Provide an 'empty query' hint
        if not any([include, exclude, equipment, sort]):
            query, sort_method = self._render_query(
                include=include,
                exclude=exclude,
                equipment=equipment,
                sort=sort
            )
            yield query, sort_method, 'empty_query'
            return

        for exact_match in [True, False]:
            query, sort_method = self._render_query(
                include=include,
                exclude=exclude,
                equipment=equipment,
                exact_match=exact_match,
                sort=sort
            )
            yield query, sort_method, None

        if include:
            for min_include_match in range(len(include), 1, -1):
                for exact_match in [True, False]:
                    query, sort_method = self._render_query(
                        include=include,
                        exclude=exclude,
                        equipment=equipment,
                        sort=sort,
                        exact_match=exact_match,
                        min_include_match=min_include_match
                    )
                    yield query, sort_method, 'partial'

            query, sort_method = self._render_query(
                include=include,
                exclude=exclude,
                equipment=equipment,
                sort=sort,
                exact_match=False,
                min_include_match=1 if include else 0
            )
            yield query, sort_method, 'match_any'

    def query(self, include, exclude, equipment, offset, limit, sort, domains,
              dietary_properties, allow_refinement=True,
              suggest_products=False):
        """
        Searching for recipes is currently supported in three different modes:

        * 'relevance' mode prioritizes matching as many ingredients as possible
        * 'ingredients' mode aims to find recipes with fewest extras required
        * 'duration' mode finds recipes that can be prepared most quickly

        In the search index, each recipe contains a list of ingredients.
        Each ingredient is indentified by the 'ingredient.product.singular'
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

        To achieve this, we use Elasticsearch's query syntax to encode
        information about the quality of each match during search execution.

        We use `constant_score` queries to store a power-of-ten score for each
        query ingredient, with the value doubled for exact matches.

        For example, in a query for `onion`, `tomato`, `garlic`:

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
            include=include,
            dietary_properties=dietary_properties
        )
        post_filter = self._generate_post_filter(
            domains=domains,
            dietary_properties=dietary_properties
        )

        queries = self._refined_queries(
            include=include,
            exclude=exclude,
            equipment=equipment,
            sort=sort
        )
        for query, sort_method, refinement in queries:
            results = self.es.search(
                index='recipes',
                body={
                    'from': offset,
                    'size': limit,
                    'query': query,
                    'sort': sort_method,
                    'aggs': aggregations,
                    'post_filter': post_filter,
                }
            )
            if not allow_refinement:
                break
            if results['aggregations']['prefilter']['doc_count'] >= 5:
                break

        recipes = []
        for result in results['hits']['hits']:
            recipe = Recipe.from_doc(result['_source'])
            recipes.append(recipe.to_dict(include))

        # TODO: Can this bucket sorting be moved into the aggregation pipeline?
        if suggest_products:
            prefilter = results['aggregations']['prefilter']
            total = prefilter['doc_count']

            products = prefilter['products']['choices']['singular']['buckets']
            products = [x for x in products if x['doc_count'] != total]
            products.sort(key=lambda x: abs(x['doc_count'] - (total / 2)))
            prefilter['products'] = {'buckets': products[:10]}

        facets = {}
        for field, content in results['aggregations']['prefilter'].items():
            if not isinstance(content, dict) or 'buckets' not in content:
                continue
            facets[field] = [
                {
                    'key': bucket['key'],
                    'count': min(bucket['doc_count'], 100),
                }
                for bucket in content['buckets']
            ]

        return {
            'authority': 'api',
            'total': min(results['hits']['total']['value'], 25 * limit),
            'results': recipes,
            'facets': facets,
            'refinements': [refinement] if recipes and refinement else []
        }

    def explore(self, include, exclude, dietary_properties):
        depth = len(set(include + exclude))
        limit = 10 if depth >= 3 else 0
        return self.query(
            include=include,
            exclude=exclude,
            equipment=[],
            offset=0,
            limit=limit,
            sort=None,
            domains=[],
            dietary_properties=dietary_properties,
            allow_refinement=False,
            suggest_products=True
        )
