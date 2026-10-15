"""mcp_server.preload: which files get listed, and that every one is read once."""

from pathlib import Path
from types import SimpleNamespace

from mcp_server.preload import imported_files, read_all


def test_lists_bytecode_over_source_and_skips_missing_files(tmp_path: Path) -> None:
    src, pyc, ext = tmp_path / "a.py", tmp_path / "a.pyc", tmp_path / "b.so"
    for f in (src, pyc, ext):
        f.write_bytes(b"x")
    modules = [
        SimpleNamespace(__cached__=str(pyc), __file__=str(src)),
        SimpleNamespace(__file__=str(ext)),  # extension module: no bytecode
        SimpleNamespace(__file__=str(tmp_path / "gone.py")),
        SimpleNamespace(),  # builtin / frozen
    ]
    files = imported_files(modules)
    assert str(pyc) in files
    assert str(ext) in files
    assert str(src) not in files
    assert not any(f.endswith("gone.py") for f in files)


def test_reads_every_file_once(tmp_path: Path) -> None:
    paths = []
    for i in range(50):
        p = tmp_path / f"f{i}"
        p.write_bytes(b"y" * (i + 1))
        paths.append(str(p))
    paths.append(str(tmp_path / "missing"))
    assert read_all(paths, threads=8) == (50, sum(range(1, 51)))
    assert read_all([], threads=8) == (0, 0)
