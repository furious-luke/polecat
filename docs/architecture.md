## Global Context

Polecat leverages a significant amount of global state to support
"compile-time" operations:

 * Populating various registries while loading models.
 * Injecting configuration options into the global configuration
   store.
 * Loading and making available the current project.
 
Instead of keeping these values all as global variables scattered
around the code, there is a centralised "context" used to store and
access global values. At present the above mentioned three categories
of global state are the only ones kept, however this can be extended
by plugins.

The primary reason behind global context is to facilitate writing
tests that require resetting, caching, or otherwise modifying the
global state. An example of this is testing the construction of
GraphQL APIs from models: each test requires a reset of the GraphQL
registries (and possibly other global state). There is no need to
track changes and roll them back as we are able to reset the global
context between tests.

Context is located in `polecat/core/context.py` and operates like a
hierarchical dictionary.
