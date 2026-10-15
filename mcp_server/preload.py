"""Read the server's import files in parallel, then start the server (ADR-017).

On Cloud Run the server's imports took 4.2-4.5 s against 0.6 s in the same
image locally, while the 53 MB of vectors load in 0.1-0.3 s: the image's files
arrive lazily, and each of the ~750 small files an import opens waits on its
own fetch. Reading them first with many threads overlaps those waits; the
imports then come from the page cache. Measured on Cloud Run: preload 0.14 s
+ imports 1.5 s, instance ready in 2.1 s instead of 4.2-5.3 s.

    python -m mcp_server.preload --write LIST        # image build: record the files
    python -m mcp_server.preload LIST [server args]  # start: read them, run the server

Only stdlib modules that are loaded anyway run before the preload.
"""

from __future__ import annotations

import importlib
import sys
import threading
import time
from collections.abc import Iterable, Sequence
from pathlib import Path

import mcp_server

THREADS = 32
CHUNK = 1 << 20


def imported_files(modules: Iterable[object]) -> list[str]:
    """The bytecode (or extension) file behind each loaded module, plus bundled native libs."""
    files: set[str] = set()
    for m in modules:
        path = getattr(m, "__cached__", None) or getattr(m, "__file__", None)
        if isinstance(path, str) and Path(path).is_file():
            files.add(path)
    # Shared libraries that wheels bundle next to their extensions (numpy.libs/…).
    for site in {p for p in sys.path if p.endswith("site-packages")}:
        for libs in Path(site).glob("*.libs"):
            files.update(str(f) for f in libs.iterdir() if f.is_file())
    return sorted(files)


def read_all(paths: Sequence[str], threads: int = THREADS) -> tuple[int, int]:
    """Read every file once with `threads` workers; returns (files read, bytes)."""
    lock = threading.Lock()
    todo = iter(paths)
    done = [0, 0]

    def worker() -> None:
        while True:
            with lock:
                path = next(todo, None)
            if path is None:
                return
            n = 0
            try:
                with Path(path).open("rb", buffering=0) as f:
                    while chunk := f.read(CHUNK):
                        n += len(chunk)
            except OSError:
                continue  # best effort: the import will report a real problem
            with lock:
                done[0] += 1
                done[1] += n

    workers = [threading.Thread(target=worker) for _ in range(min(threads, len(paths)) or 1)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    return done[0], done[1]


def main(argv: list[str]) -> int:
    if argv[:1] == ["--write"]:
        importlib.import_module("mcp_server.server")  # load everything the server loads
        files = imported_files(list(sys.modules.values()))
        Path(argv[1]).write_text("\n".join(files) + "\n")
        print(f"preload list: {len(files)} files -> {argv[1]}", file=sys.stderr)
        return 0
    if not argv:
        print("usage: python -m mcp_server.preload (--write LIST | LIST [server args])")
        return 2
    t0 = time.perf_counter()
    paths = Path(argv[0]).read_text().split()
    read_all(paths)
    now = time.perf_counter()
    mcp_server.STARTUP_PHASES["preload"] = round(now - t0, 3)
    mcp_server.IMPORT_T0 = now  # "imports" then measures the imports alone
    from mcp_server.server import main as serve

    return serve(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
