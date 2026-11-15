class RegistryUnavailable(Exception):
    """The registry (e.g. the blockchain node) cannot be reached.

    Lives in the application layer: adapters depend on the core, not the other way round.
    """
