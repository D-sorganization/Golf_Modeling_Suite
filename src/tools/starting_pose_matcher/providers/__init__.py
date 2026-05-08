"""Starting-pose matcher provider registry.

Concrete provider modules are intentionally not imported here.  Use
``providers.registry.create_provider()`` so optional engine dependencies remain
lazy and core-only environments can start the matcher.
"""

from src.tools.starting_pose_matcher.providers.registry import (
    ProviderRegistration,
    create_provider,
    get_registration,
    list_provider_ids,
    list_provider_metadata,
)

__all__ = [
    "ProviderRegistration",
    "create_provider",
    "get_registration",
    "list_provider_ids",
    "list_provider_metadata",
]
