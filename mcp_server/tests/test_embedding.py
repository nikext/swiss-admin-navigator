"""QueryEmbedder: format from the index meta, cache, breaker. The API is faked."""

from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from mcp_server import embedding
from mcp_server.embedding import (
    EmbeddingConfigError,
    EmbeddingUnavailableError,
    QueryEmbedder,
)

SPACE = {
    "model": "gemini-embedding-2",
    "location": "eu",
    "input_format": "instruction",
    "query_template": "task: search result | query: {text}",
    "dims": 4,
}


class FakeModels:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.fail = False

    async def embed_content(self, *, model: str, contents: list[str], config: Any) -> Any:
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self.fail:
            raise TimeoutError
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[3.0, 4.0, 0.0, 0.0])])


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeModels:
    models = FakeModels()

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            self.aio = SimpleNamespace(models=models)

    monkeypatch.setattr(embedding.genai, "Client", FakeClient)
    return models


async def test_query_uses_the_index_template_and_dims(fake: FakeModels) -> None:
    e = QueryEmbedder(SPACE, "p", {})
    v = await e.embed("  Mietkaution   Wohnung ")
    np.testing.assert_allclose(v, [0.6, 0.8, 0.0, 0.0])
    (call,) = fake.calls
    assert call["contents"] == ["task: search result | query: Mietkaution Wohnung"]
    assert call["config"].output_dimensionality == 4
    assert call["config"].task_type is None
    await e.embed("Mietkaution Wohnung")  # whitespace-normalised cache hit
    assert len(fake.calls) == 1


async def test_task_type_spaces_send_the_raw_query(fake: FakeModels) -> None:
    space = SPACE | {"input_format": "task_type", "query_task_type": "RETRIEVAL_QUERY"}
    await QueryEmbedder(space, "p", {}).embed("Mietkaution")
    assert fake.calls[0]["contents"] == ["Mietkaution"]
    assert fake.calls[0]["config"].task_type == "RETRIEVAL_QUERY"


async def test_breaker_skips_the_endpoint_after_a_failure(fake: FakeModels) -> None:
    e = QueryEmbedder(SPACE, "p", {}, cooldown_s=60)
    fake.fail = True
    with pytest.raises(TimeoutError):
        await e.embed("a")
    with pytest.raises(EmbeddingUnavailableError):
        await e.embed("b")
    assert len(fake.calls) == 1  # the second query never hit the endpoint
    e._down_until = 0.0
    fake.fail = False
    assert (await e.embed("c")).shape == (4,)


def test_env_can_move_the_endpoint_but_not_change_the_model(fake: FakeModels) -> None:
    assert QueryEmbedder(SPACE, "p", {"EMBEDDING_LOCATION": "global"}).location == "global"
    assert QueryEmbedder(SPACE, "p", {"EMBEDDING_MODEL": "gemini-embedding-2"}).model
    with pytest.raises(EmbeddingConfigError, match="index was built with"):
        QueryEmbedder(SPACE, "p", {"EMBEDDING_MODEL": "gemini-embedding-001"})


async def test_warm_up_calls_the_endpoint_once_and_never_trips_the_breaker(
    fake: FakeModels,
) -> None:
    e = QueryEmbedder(SPACE, "p", {})
    fake.fail = True
    await e.warm()  # logs, does not raise
    assert e._down_until == 0.0
    fake.fail = False
    await e.warm()
    assert len(fake.calls) == 2
    assert e._cache == {}  # warm-up results are not cached as a query
