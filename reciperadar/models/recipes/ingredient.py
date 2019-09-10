from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from reciperadar.models.base import Searchable, Storable
from reciperadar.models.recipes.product import IngredientProduct


class RecipeIngredient(Storable, Searchable):
    __tablename__ = 'recipe_ingredients'

    fk = ForeignKey('recipes.id', ondelete='cascade')
    recipe_id = Column(String, fk, index=True)

    id = Column(String, primary_key=True)
    description = Column(String)
    product = relationship(
        'IngredientProduct',
        backref='recipe_ingredient',
        uselist=False,
        passive_deletes='all'
    )

    quantity = Column(Float)
    quantity_parser = Column(String)
    units = Column(String)
    units_parser = Column(String)
    verb = Column(String)

    @staticmethod
    def from_doc(doc):
        ingredient_id = doc.get('id') or RecipeIngredient.generate_id()
        return RecipeIngredient(
            id=ingredient_id,
            description=doc['description'].strip(),
            product=IngredientProduct.from_doc(doc['product']),
            quantity=doc.get('quantity'),
            units=doc.get('units'),
            verb=doc.get('verb')
        )

    def to_dict(self, include=None):
        tokens = []
        if self.quantity:
            tokens.append({
                'type': 'quantity',
                'value': self.quantity,
            })
            tokens.append({
                'type': 'text',
                'value': ' ',
            })
        if self.units:
            tokens.append({
                'type': 'units',
                'value': self.units,
            })
            tokens.append({
                'type': 'text',
                'value': ' ',
            })
        tokens.append(self.product.to_dict(include))
        return {'tokens': tokens}

    def to_doc(self):
        data = super().to_doc()
        data['product'] = self.product.to_doc()
        return data

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
                        {'match': {'ingredients.product.product': prefix}},
                        {'prefix': {'ingredients.product.product': prefix}}
                      ]
                    }
                  },
                  'aggregations': {
                    # retrieve the top products in singular pluralization
                    'product': {
                      'terms': {
                        'field': 'ingredients.product.singular',
                        'min_doc_count': 5,
                        'size': 10
                      },
                      'aggregations': {
                        # count products that were plural in the source recipe
                        'plurality': {
                          'filter': {
                            'match': {'ingredients.product.is_plural': True}
                          },
                          'aggregations': {
                            # return the plural word form in the results
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
          }
        }
        results = self.es.search(index=self.noun, body=query)['aggregations']
        results = results['ingredients']['products']['product']['buckets']

        # iterate through the suggestions and determine whether to display
        # the singular or plural form of the word based on how frequently
        # each form is used in the overall recipe corpus
        suggestions = []
        for result in results:
            total_count = result['doc_count']
            plural_count = result['plurality']['doc_count']
            plural_docs = result['plurality']['plural']['buckets']
            plural_wins = plural_count > total_count - plural_count

            suggestion_doc = plural_docs[0] if plural_wins else result
            suggestions.append(IngredientProduct(
                product=suggestion_doc['key'],
                singular=result['key']
            ))

        suggestions.sort(key=lambda s: (
            s.product != prefix,  # exact matches first
            not s.product.startswith(prefix),  # prefix matches next
            len(s.product)),  # sort remaining matches by length
        )
        return [{
            'product': suggestion.product,
            'category': suggestion.category,
            'singular': suggestion.singular
        } for suggestion in suggestions]