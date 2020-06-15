from urllib.parse import urljoin

import logging
from polecat.model import default_blueprint

from ..model import omit

from .schema import RestSchema, RestView

logger = logging.getLogger(__name__)


class RestSchemaBuilder:
    def build(self):
        logger.debug('Building REST schema')
        self.post_build_hooks = []
        self.types = []
        self.mutations = {}
        self.build_mutations()
        self.run_post_build_hooks()
        return RestSchema(
            routes=self.mutations
        )

    def build_mutations(self):
        logger.debug('Building GraphQL mutations')
        for mutation in self.iter_mutations():
            builder_class = getattr(mutation, 'builder', MutationBuilder)
            builder = builder_class(self)
            builder.build(mutation)

    def iter_mutations(self):
        for mutation in default_blueprint.iter_mutations():
            yield mutation

    def run_post_build_hooks(self):
        for hook in self.post_build_hooks:
            hook()


class MutationBuilder:
    def __init__(self, schema_builder):
        self.schema_builder = schema_builder

    def build(self, mutation):
        if self.is_rest_mutation(mutation):
            self.schema_builder.mutations.update(self.build_mutations(mutation))

    def is_rest_mutation(self, mutation):
        return hasattr(mutation, 'route')

    def build_mutations(self, mutation):
        mutations = {}
        if not mutation.omit & omit.ALL:
            route = self.mutation_route(mutation)
            mutations[route] = RestView(mutation)
        return mutations

    def mutation_route(self, mutation):
        return urljoin('/rest/', mutation.route)
