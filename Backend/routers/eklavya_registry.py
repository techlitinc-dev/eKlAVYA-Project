"""
eKlAVYA Router Registry

Single place where all eKlAVYA API routers are enumerated. main.py includes
every returned router under API_V1_PREFIX (/api/v1).

During incremental development, missing router modules are logged and
skipped; final builds run in strict mode so a missing router fails fast.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import importlib
import logging

logger = logging.getLogger(__name__)

# Set to True in final builds: every router module must import cleanly.
STRICT_IMPORTS = True

EKLAVYA_ROUTER_MODULES = [
    "routers.syllabus_router",
    "routers.planner_router",
    "routers.notes_router",
    "routers.mindmap_router",
    "routers.scan_router",
    "routers.speech_router",
    "routers.communication_router",
    "routers.teacher_router",
    "routers.parent_router",
]


def get_eklavya_routers() -> list:
    """Import and return all available eKlAVYA API routers."""
    routers = []
    missing = []
    for module_name in EKLAVYA_ROUTER_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
            if STRICT_IMPORTS:
                raise
            continue
        routers.append(module.router)

    if missing:
        logger.warning(
            "eKlAVYA routers not yet available (skipped): %s", ", ".join(missing)
        )
    return routers
