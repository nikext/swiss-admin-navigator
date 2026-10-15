"""Hybrid retrieval over index.sqlite: FTS5 BM25 + dense vectors, fused with RRF.

Used by the MCP server's `search_law` and by the retrieval eval (E4), so the
eval measures exactly what is served. Only in-force articles are indexed as
chunks, so search never returns repealed or omitted text (DATA.md §3).

Results are unique *articles*: chunks of a split article and the language
versions of one article collapse into the best-ranked one, so k=8 means eight
different provisions.
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np

Mode = Literal["bm25", "dense", "hybrid"]

# Function words only: BM25's IDF already discounts frequent legal vocabulary,
# and words like "darf"/"muss"/"peut" can matter.
_STOP_DE = """der die das den dem des ein eine einer eines einem einen und oder aber wenn als wie
was wer wo ich du er sie es wir ihr mein meine meinen meinem meiner mir mich dir
dich sich ist sind bin bist war habe hast hat haben werde wird werden kann können zu
zum zur von vom mit auf in im an am aus bei für über unter nach vor nicht kein keine
noch auch so da dass ob um"""
_STOP_FR = """le la les un une des du de et ou mais si que qui quoi quel quelle quels quelles je
tu il elle on nous vous ils elles me te se mon ma mes ton ta son sa ses notre votre
leur est sont suis ai as avons avez ont être avoir peut dans en au aux par pour sur
avec ne pas plus ce cet cette ces qu"""
_STOP_IT = """il lo gli una uno della dello delle degli dei del di ma se che chi cui io tu lui lei
noi voi loro mi ti ci vi si mio mia miei mie suo sua sono ho hai ha abbiamo avete
hanno da dal dalla nel nella nei con su per tra fra non più questo questa"""
_STOP_EN = """the an of and or but if then what which who whom how when where why you he she it we
they me my mine your his her its our their is are was were be been being am do does
did have has had can could may might shall should will would to from in on at by for
with about into not no this that these those there here as so"""
STOPWORDS = frozenset(
    w for block in (_STOP_DE, _STOP_FR, _STOP_IT, _STOP_EN) for w in block.split()
)
_WORD = re.compile(r"\w+", re.UNICODE)
_BLOCKS = {"de": _STOP_DE, "fr": _STOP_FR, "it": _STOP_IT, "en": _STOP_EN}
# Function words that belong to one language only ("le" is FR, "il" is FR and IT: dropped).
# Extra markers for guess_lang only (not stopwords: BM25 is unaffected).
_HINTS = {
    "de": "wann warum welche welcher welches darf muss ab",
    "fr": "comment quand combien puis dois",
    "it": "un la e come quando quanto quale cosa posso devo",
    "en": "can must should",
}
_LANG_WORDS = {
    lang: set(f"{block} {_HINTS[lang]}".split()).difference(
        *(f"{b} {_HINTS[o]}".split() for o, b in _BLOCKS.items() if o != lang)
    )
    for lang, block in _BLOCKS.items()
}


def guess_lang(query: str) -> str | None:
    """The query's language from function words only it uses, or None if unclear.

    Good enough to pick which language version of a hit to *display*; ranking
    never depends on it.
    """
    words = _WORD.findall(query.lower())
    counts = {lang: sum(w in vocab for w in words) for lang, vocab in _LANG_WORDS.items()}
    best = max(counts, key=lambda k: counts[k])
    ranked = sorted(counts.values(), reverse=True)
    return best if ranked[0] > 0 and ranked[0] > ranked[1] else None


@dataclass(frozen=True)
class SearchConfig:
    mode: Mode = "hybrid"
    tokenizer: str | None = None  # None: the index's default
    header: bool = True  # BM25 also matches the contextual header column
    prefix: bool = False  # unicode61 only: "kündigung"* also matches "kündigungsschutz"
    space: str | None = None  # None: the index's default vector space
    dims: int | None = None  # Matryoshka-truncate the space (None: as stored)
    depth: int = 50  # candidate articles per retriever before fusion
    rrf_k: int = 60
    bm25_weight: float = 1.0  # RRF weight of the BM25 list (dense has 1.0)


@dataclass
class Hit:
    chunk: int  # chunk rowid
    sr: str
    eid: str
    lang: str
    score: float
    ranks: dict[str, int] = field(default_factory=dict)  # retriever -> 1-based rank


def query_terms(query: str, tokenizer: str) -> list[str]:
    """Lowercased content words; trigram needs >= 3 chars to match anything."""
    min_len = 3 if tokenizer == "trigram" else 2
    words = (w for w in _WORD.findall(query.lower()) if len(w) >= min_len and w not in STOPWORDS)
    return list(dict.fromkeys(words))


def fts_query(query: str, tokenizer: str, prefix: bool = False, header: bool = True) -> str | None:
    """An FTS5 MATCH expression: any content word, as quoted phrases."""
    terms = query_terms(query, tokenizer)
    if not terms:
        return None
    star = "*" if prefix and tokenizer != "trigram" else ""
    expr = " OR ".join(f'"{t.replace(chr(34), chr(34) * 2)}"{star}' for t in terms)
    return expr if header else f"body : ({expr})"


class Index:
    """Read-only view of index.sqlite. One SQLite connection per thread."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"index not found: {self.path} (run `make index`)")
        self._local = threading.local()
        db = self.db
        self.meta: dict[str, Any] = {k: json.loads(v) for k, v in db.execute("SELECT * FROM meta")}
        rows = db.execute("SELECT rowid, sr, lang, eid FROM chunks ORDER BY rowid").fetchall()
        n = (rows[-1][0] + 1) if rows else 1
        self.chunk_sr = np.empty(n, dtype=object)
        self.chunk_lang = np.empty(n, dtype=object)
        self.chunk_eid = np.empty(n, dtype=object)
        for rowid, sr, lang, eid in rows:
            self.chunk_sr[rowid], self.chunk_lang[rowid], self.chunk_eid[rowid] = sr, lang, eid
        self._spaces: dict[tuple[str, int | None], tuple[np.ndarray, np.ndarray]] = {}
        self._lock = threading.Lock()

    @property
    def db(self) -> sqlite3.Connection:
        conn = getattr(self._local, "db", None)
        if conn is None:
            uri = f"file:{self.path.resolve()}?mode=ro&immutable=1"
            conn = self._local.db = sqlite3.connect(uri, uri=True, check_same_thread=False)
        return conn

    def space_spec(self, name: str | None = None) -> dict[str, Any]:
        name = name or self.meta.get("default_space")
        for spec in self.meta.get("spaces", []):
            if spec["name"] == name:
                return spec
        raise KeyError(f"no vector space {name!r} in {self.path}")

    def space(
        self, name: str | None = None, dims: int | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        """(rowids, matrix) of a vector space, loaded once and kept in memory."""
        resolved: str = self.space_spec(name)["name"]
        key = (resolved, dims)
        with self._lock:
            if key not in self._spaces:
                n, d, rowids, blob = self.db.execute(
                    "SELECT n, dims, rowids, matrix FROM vector_spaces WHERE name = ?", (resolved,)
                ).fetchone()
                matrix = np.frombuffer(blob, dtype=np.float32).reshape(n, d)
                if dims and dims < d:
                    matrix = matrix[:, :dims]
                    matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
                self._spaces[key] = (np.frombuffer(rowids, dtype=np.int32), matrix)
            return self._spaces[key]

    def tokenizers(self) -> list[str]:
        return list(self.meta.get("tokenizers") or [])


def served_config(index: Index, env: dict[str, str] | None = None) -> SearchConfig:
    """What `search_law` serves: the index's default mode, unless SEARCH_MODE overrides it."""
    mode: Any = (env or {}).get("SEARCH_MODE") or index.meta.get("default_mode") or "dense"
    if mode not in ("bm25", "dense", "hybrid"):
        raise ValueError(f"SEARCH_MODE must be bm25, dense or hybrid, not {mode!r}")
    return SearchConfig(mode=mode)


class Searcher:
    def __init__(self, index: Index, config: SearchConfig | None = None) -> None:
        self.index = index
        self.config = config or SearchConfig()
        self.tokenizer = self.config.tokenizer or index.meta.get("default_tokenizer") or "trigram"
        if self.config.mode != "dense" and self.tokenizer not in index.tokenizers():
            raise ValueError(f"index has no fts_{self.tokenizer} table")

    def _mask(self, rowids: np.ndarray, lang: str | None, srs: Sequence[str] | None) -> np.ndarray:
        ok = np.ones(len(rowids), dtype=bool)
        if lang:
            ok &= self.index.chunk_lang[rowids] == lang
        if srs:
            ok &= np.isin(self.index.chunk_sr[rowids], list(srs))
        return ok

    def bm25(
        self, query: str, lang: str | None, srs: Sequence[str] | None
    ) -> list[tuple[int, float]]:
        expr = fts_query(query, self.tokenizer, self.config.prefix, self.config.header)
        if expr is None:
            return []
        table = f"fts_{self.tokenizer}"
        where, params = [f"{table} MATCH ?"], [expr]
        if lang:
            where.append("c.lang = ?")
            params.append(lang)
        if srs:
            where.append(f"c.sr IN ({','.join('?' * len(srs))})")
            params += list(srs)
        sql = (
            f"SELECT f.rowid, bm25({table}, 1.0, 1.0) AS s FROM {table} f "  # noqa: S608
            f"JOIN chunks c ON c.rowid = f.rowid WHERE {' AND '.join(where)} ORDER BY s LIMIT ?"
        )
        try:
            rows = self.index.db.execute(sql, [*params, self.config.depth * 6]).fetchall()
        except sqlite3.OperationalError:  # e.g. an FTS5 syntax corner case
            return []
        return [(int(r), -float(s)) for r, s in rows]

    def dense(
        self, qvec: np.ndarray, lang: str | None, srs: Sequence[str] | None
    ) -> list[tuple[int, float]]:
        rowids, matrix = self.index.space(self.config.space, self.config.dims)
        q = np.asarray(qvec, dtype=np.float32)[: matrix.shape[1]]
        q = q / (np.linalg.norm(q) or 1.0)
        scores = matrix @ q
        if lang or srs:
            scores = np.where(self._mask(rowids, lang, srs), scores, -np.inf)
        limit = min(self.config.depth * 6, len(scores))
        top = np.argpartition(-scores, limit - 1)[:limit] if limit else np.array([], dtype=int)
        top = top[np.argsort(-scores[top])]
        return [(int(rowids[i]), float(scores[i])) for i in top if np.isfinite(scores[i])]

    def _collapse(
        self, ranked: list[tuple[int, float]]
    ) -> list[tuple[tuple[str, str], int, float]]:
        """Best chunk per article (sr, eid), in rank order, at most `depth` articles."""
        out: dict[tuple[str, str], tuple[int, float]] = {}
        for rowid, score in ranked:
            key = (self.index.chunk_sr[rowid], self.index.chunk_eid[rowid])
            if key not in out:
                out[key] = (rowid, score)
                if len(out) >= self.config.depth:
                    break
        return [(k, r, s) for k, (r, s) in out.items()]

    def search(
        self,
        query: str,
        qvec: np.ndarray | None = None,
        lang: str | None = None,
        srs: Sequence[str] | None = None,
        k: int = 8,
    ) -> list[Hit]:
        mode = self.config.mode
        lists: dict[str, list[tuple[tuple[str, str], int, float]]] = {}
        if mode in ("bm25", "hybrid"):
            lists["bm25"] = self._collapse(self.bm25(query, lang, srs))
        if mode in ("dense", "hybrid"):
            if qvec is None:
                raise ValueError(f"mode {mode!r} needs a query vector")
            lists["dense"] = self._collapse(self.dense(qvec, lang, srs))

        if mode != "hybrid":
            ((name, ranked),) = lists.items()
            return [
                Hit(rowid, key[0], key[1], self.index.chunk_lang[rowid], score, {name: i + 1})
                for i, (key, rowid, score) in enumerate(ranked[:k])
            ]

        fused: dict[tuple[str, str], Hit] = {}
        weights = {"bm25": self.config.bm25_weight, "dense": 1.0}
        for name, ranked in lists.items():
            for i, (key, rowid, _) in enumerate(ranked):
                hit = fused.get(key)
                if hit is None:
                    hit = fused[key] = Hit(rowid, key[0], key[1], self.index.chunk_lang[rowid], 0.0)
                hit.score += weights[name] / (self.config.rrf_k + i + 1)
                hit.ranks[name] = i + 1
        return sorted(fused.values(), key=lambda h: -h.score)[:k]
