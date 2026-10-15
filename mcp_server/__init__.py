"""swiss-law MCP server (see server.py)."""

import time

# Taken before any of the server's third-party imports: the "imports" startup phase.
IMPORT_T0 = time.perf_counter()
# Phases before the imports (mcp_server.preload), logged with the others in "ready".
STARTUP_PHASES: dict[str, float] = {}
