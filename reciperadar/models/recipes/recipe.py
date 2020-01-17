from pymmh3 import hash_bytes
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from reciperadar.models.base import Searchable, Storable
from reciperadar.models.recipes.direction import RecipeDirection
from reciperadar.models.recipes.ingredient import RecipeIngredient


class Recipe(Storable, Searchable):
    __tablename__ = 'recipes'

    id = Column(String, primary_key=True)
    title = Column(String)
    src = Column(String)
    domain = Column(String)
    image_src = Column(String)
    time = Column(Integer)
    servings = Column(Integer)
    rating = Column(Float)
    ingredients = relationship(
        'RecipeIngredient',
        backref='recipe',
        passive_deletes='all'
    )
    directions = relationship(
        'RecipeDirection',
        backref='recipe',
        passive_deletes='all'
    )

    indexed_at = Column(DateTime)

    @property
    def noun(self):
        return 'recipes'

    @property
    def url(self):
        return f'/#action=view&id={self.id}'

    @property
    def products(self):
        unique_products = {
            ingredient.product.singular: ingredient.product
            for ingredient in self.ingredients
        }
        return list(unique_products.values())

    @staticmethod
    def from_doc(doc):
        src_hash = hash_bytes(doc['src']).encode('utf-8')
        recipe_id = doc.get('id') or Recipe.generate_id(src_hash)
        return Recipe(
            id=recipe_id,
            title=doc['title'],
            src=doc['src'],
            domain=doc['domain'],
            image_src=doc.get('image_src'),
            ingredients=[
                RecipeIngredient.from_doc(ingredient)
                for ingredient in doc['ingredients']
                if ingredient['description'].strip()
            ],
            directions=[
                RecipeDirection.from_doc(direction)
                for direction in doc.get('directions') or []
                if direction['description'].strip()
            ],
            servings=doc['servings'],
            time=doc['time'],
            rating=doc['rating']
        )

    def to_dict(self, include=None):
        return {
            'id': self.id,
            'title': self.title,
            'time': self.time,
            'ingredients': [
                ingredient.to_dict(include)
                for ingredient in self.ingredients
            ],
            'directions': [
                direction.to_dict()
                for direction in self.directions
            ],
            'servings': self.servings,
            'rating': self.rating,
            'src': self.src,
            'domain': self.domain,
            'url': self.url,
            'image_url': self.image_path,
        }

    @property
    def image_path(self):
        return f'images/recipes/{self.id}.png'

    @property
    def contents(self):
        contents = set()
        for product in self.products:
            contents |= set(product.contents or [])
        return list(contents)

    def to_doc(self):
        data = super().to_doc()
        data['directions'] = [
            direction.to_doc()
            for direction in self.directions
        ]
        data['ingredients'] = [
            ingredient.to_doc()
            for ingredient in self.ingredients
        ]
        data['contents'] = self.contents
        data['product_count'] = len(self.products)
        return data

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
    def _generate_include_exact(include):
        return [{
            'nested': {
                'path': 'ingredients',
                'query': {
                    'constant_score': {
                        'boost': pow(10, idx) * 2,
                        'filter': {
                            'match': {'ingredients.product.product': inc}
                        }
                    }
                }
            }
        } for idx, inc in enumerate(reversed(include))]

    @staticmethod
    def _generate_exclude_clause(exclude):
        # match any ingredients in the exclude list
        return [{'match': {'contents': exc}} for exc in exclude]

    @staticmethod
    def _generate_equipment_clause(equipment):
        return [
            {'match': {'directions.equipment.equipment': item}}
            for item in equipment
        ]

    @staticmethod
    def _generate_sort_params(include, sort):
        # don't score relevance searches if no query ingredients are provided
        if sort == 'relevance' and not include:
            return {'script': '0', 'order': 'desc'}

        preamble = '''
            def product_count = doc.product_count.value;
            def exact_found_count = 0;
            def found_count = 0;
            for (def score = (long) _score; score > 0; score /= 10) {
                if (score % 10 > 2) exact_found_count++;
                if (score % 10 > 0) found_count++;
            }
            def missing_count = product_count - found_count;

            def missing_ratio = missing_count / product_count;
            def normalized_rating = doc.rating.value / 10;
        '''
        sort_configs = {
            # rank: number of ingredient matches
            # tiebreak: recipe rating
            'relevance': {
                'script': f'{preamble} (found_count * 2 + exact_found_count) + normalized_rating',
                'order': 'desc'
            },

            # rank: number of missing ingredients
            # tiebreak: recipe rating
            'ingredients': {
                'script': f'{preamble} missing_count + normalized_rating',
                'order': 'asc'
            },

            # rank: preparation time
            # tiebreak: percentage of missing ingredients
            'duration': {
                'script': f'{preamble} doc.time.value + missing_ratio',
                'order': 'asc'
            },
        }
        return sort_configs[sort]

    def _render_query(self, include, exclude, equipment, sort,
                      match_all=True, match_exact=False):
        include_clause = self._generate_include_clause(include)
        include_exact = self._generate_include_exact(include)
        exclude_clause = self._generate_exclude_clause(exclude)
        equipment_clause = self._generate_equipment_clause(equipment)
        sort_params = self._generate_sort_params(include, sort)

        must = include_clause if match_all else []
        should = include_exact if match_all and match_exact else include_clause
        must_not = exclude_clause
        filter = equipment_clause + [
            {'range': {'time': {'gte': 5}}},
            {'range': {'product_count': {'gt': 0}}},
        ]

        return {
            'function_score': {
                'boost_mode': 'replace',
                'query': {
                    'bool': {
                        'must': must,
                        'should': should,
                        'must_not': must_not,
                        'filter': filter,
                        'minimum_should_match': None if match_all else 1
                    }
                },
                'script_score': {'script': {'source': sort_params['script']}}
            }
        }, [{'_score': sort_params['order']}]

    def _refined_queries(self, include, exclude, equipment, sort_order):
        if include:
            query, sort = self._render_query(
                include=include,
                exclude=exclude,
                equipment=equipment,
                sort=sort_order,
                match_exact=True
            )
            yield query, sort, None

        query, sort = self._render_query(
            include=include,
            exclude=exclude,
            equipment=equipment,
            sort=sort_order
        )
        yield query, sort, None

        item_count = len(include)
        if item_count > 3:
            for _ in range(item_count):
                removed = include.pop(0)
                query, sort = self._render_query(
                    include=include,
                    exclude=exclude,
                    equipment=equipment,
                    sort=sort_order
                )
                yield query, sort, f'removed:{removed}'
                include.append(removed)

        if item_count > 1:
            query, sort = self._render_query(
                include=include,
                exclude=exclude,
                equipment=equipment,
                sort=sort_order,
                match_all=False
            )
            yield query, sort, 'match_any'

    def search(self, include, exclude, equipment, offset, limit, sort_order):
        offset = max(0, offset)
        limit = max(1, limit)
        limit = min(25, limit)
        sort_order = sort_order or 'relevance'

        queries = self._refined_queries(
            include=include,
            exclude=exclude,
            equipment=equipment,
            sort_order=sort_order
        )
        for query, sort, refinement in queries:
            results = self.es.search(
                index=self.noun,
                body={
                    'from': offset,
                    'size': limit,
                    'query': query,
                    'sort': sort,
                }
            )
            if results['hits']['total']['value']:
                break

        recipes = []
        for result in results['hits']['hits']:
            recipe = Recipe.from_doc(result['_source'])
            recipes.append(recipe.to_dict(include))

        return {
            'authority': 'api',
            'total': min(results['hits']['total']['value'], 25 * limit),
            'results': recipes,
            'refinements': [refinement] if refinement else []
        }
