from polecat.graphql import build_graphql_schema
from polecat.graphql.utils import print_schema
from polecat.model import Model, RelatedField, omit


class AllOmitted(Model):
    class Meta:
        omit = omit.ALL


class ListOmitted(Model):
    all = RelatedField(AllOmitted)

    class Meta:
        omit = omit.LIST


class GetOmitted(Model):
    list = RelatedField(ListOmitted)

    class Meta:
        omit = omit.GET


class CreateOmitted(Model):
    class Meta:
        omit = omit.CREATE


class UpdateOmitted(Model):
    class Meta:
        omit = omit.UPDATE


def test_omit():
    schema = build_graphql_schema()
    # print_schema(schema)
    omitted_types = ('AllOmitted',)
    for type in omitted_types:
        assert type not in schema.type_map
    queries = schema.type_map['Query']
    omitted_queries = (
        'allAllOmitted', 'getAllOmitted',
        'allListOmitted',
        'getGetOmitted'
    )
    for query in omitted_queries:
        assert query not in queries.fields
    mutations = schema.type_map['Mutation']
    omitted_mutations = (
        'createAllOmitted', 'updateAllOmitted',
        'createCreateOmitted',
        'updateUpdateOmitted'
    )
    for mutation in omitted_mutations:
        assert mutation not in mutations.fields
