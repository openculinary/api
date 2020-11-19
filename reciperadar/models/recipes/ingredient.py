from reciperadar import db
from reciperadar.models.base import Searchable, Storable
from reciperadar.models.recipes.nutrition import IngredientNutrition
from reciperadar.models.recipes.product import Product


class RecipeIngredient(Storable, Searchable):
    __tablename__ = 'recipe_ingredients'

    recipe_fk = db.ForeignKey('recipes.id', ondelete='cascade')
    recipe_id = db.Column(db.String, recipe_fk, index=True)

    product_fk = db.ForeignKey('products.id', deferrable=True)
    product_id = db.Column(db.String, product_fk, index=True)

    id = db.Column(db.String, primary_key=True)
    index = db.Column(db.Integer)
    description = db.Column(db.String)
    markup = db.Column(db.String)

    product = db.relationship(
        'Product',
        uselist=False,
        passive_deletes='all'
    )
    nutrition = db.relationship(
        'IngredientNutrition',
        backref='recipe_ingredient',
        uselist=False,
        passive_deletes='all'
    )

    magnitude = db.Column(db.Float)
    magnitude_parser = db.Column(db.String)
    units = db.Column(db.String)
    units_parser = db.Column(db.String)
    product_is_plural = db.Column(db.Boolean)
    product_parser = db.Column(db.String)
    verb = db.Column(db.String)

    @property
    def product_name(self):
        if self.product_is_plural:
            return self.product.plural
        else:
            return self.product.singular

    @staticmethod
    def from_doc(doc):
        ingredient_id = doc.get('id') or RecipeIngredient.generate_id()
        nutrition = doc.get('nutrition')
        return RecipeIngredient(
            id=ingredient_id,
            index=doc['index'],
            description=doc['description'].strip(),
            markup=doc.get('markup'),
            product=Product.from_doc(doc['product']),
            product_id=doc['product'].get('id'),
            product_is_plural=doc.get('product_is_plural'),
            product_parser=doc['product'].get('product_parser'),
            nutrition=IngredientNutrition.from_doc(nutrition)
            if nutrition else None,
            magnitude=doc.get('magnitude'),
            magnitude_parser=doc.get('magnitude_parser'),
            units=doc.get('units'),
            units_parser=doc.get('units_parser'),
            verb=doc.get('verb'),
        )

    def to_dict(self, include=None):
        return {
            'markup': self.markup,
            'product': {
                **self.product.to_dict(include),
                # TODO: would a 'countable' flag on products be preferable?
                **{'name': self.product_name},
                # TODO: these fields are provided for backwards-compatbility
                **{
                    'product_id': self.product.id,
                    'product': self.product_name,
                },
            },
            'quantity': {
                'magnitude': self.magnitude,
                'units': self.units,
            }
        }

    @property
    def noun(self):
        return 'recipes'

    def autosuggest(self, prefix):
        prefix = prefix.lower()
        query = {
          'aggregations': {
            # aggregate across all nested ingredient documents
            'ingredients': {
              'nested': {'path': 'ingredients'},
              'aggregations': {
                # filter to product names which match the user search
                'products': {
                  'filter': {
                    'bool': {
                      'should': [
                        {
                          'match': {
                            'ingredients.product_name.autocomplete': {
                              'query': prefix,
                              'operator': 'AND',
                              'fuzziness': 'AUTO'
                            }
                          }
                        },
                        {'prefix': {'ingredients.product_name': prefix}}
                      ]
                    }
                  },
                  'aggregations': {
                    # retrieve the top products in singular pluralization
                    'product_id': {
                      'terms': {
                        'field': 'ingredients.product.id',
                        'min_doc_count': 5,
                        'size': 10
                      },
                      'aggregations': {
                        # count products that were plural in the source recipe
                        'plurality': {
                          'filter': {
                            'match': {'ingredients.product_is_plural': True}
                          }
                        },
                        # retrieve a category for each ingredient
                        'category': {
                          'terms': {
                            'field': 'ingredients.product.category',
                            'size': 1
                          }
                        },
                        'singular': {
                          'terms': {
                            'field': 'ingredients.product.singular',
                            'size': 1
                          }
                        },
                        'plural': {
                          'terms': {
                            'field': 'ingredients.product.plural',
                            'size': 1
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        results = self.es.search(index=self.noun, body=query)['aggregations']
        results = results['ingredients']['products']['product_id']['buckets']

        # iterate through the suggestions and determine whether to display
        # the singular or plural form of the word based on how frequently
        # each form is used in the overall recipe corpus
        suggestions = []
        for result in results:
            total_count = result['doc_count']
            plural_count = result['plurality']['doc_count']
            plural_wins = plural_count > total_count - plural_count

            product_id = result['key']
            category = (result['category']['buckets'] or [{}])[0].get('key')
            singular = (result['singular']['buckets'] or [{}])[0].get('key')
            plural = (result['plural']['buckets'] or [{}])[0].get('key')

            product = Product(
                id=product_id,
                category=category,
                singular=singular,
                plural=plural,
            )
            product.name = plural if plural_wins else singular
            suggestions.append(product)

        suggestions.sort(key=lambda s: (
            s.name != prefix,  # exact matches first
            not s.name.startswith(prefix),  # prefix matches next
            len(s.name)),  # sort remaining matches by length
        )
        return [{
            'id': suggestion.id,
            'name': suggestion.name,
            'category': suggestion.category,
            'singular': suggestion.singular,
            'plural': suggestion.plural,
            # TODO: these fields are provided for backwards-compatbility
            'product_id': suggestion.id,
            'product': suggestion.name,
        } for suggestion in suggestions]
