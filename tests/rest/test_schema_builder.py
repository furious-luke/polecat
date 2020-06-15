from polecat.rest.schema_builder import RestSchemaBuilder


def test_schema_builder():
    schema = RestSchemaBuilder().build()
    assert len(schema.routes) > 0
