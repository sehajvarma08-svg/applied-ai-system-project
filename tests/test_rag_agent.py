import json
from types import SimpleNamespace

import pytest

from src.agent import MusicTools, AgentResult, build_tools, run_agent
from src.rag import Retriever, load_chunks, tokenize
from src.recommender import load_songs


@pytest.fixture(scope="module")
def retriever():
    return Retriever.from_directory()


@pytest.fixture()
def tools(retriever):
    return MusicTools(load_songs("data/songs.csv"), retriever)


def test_chunks_are_split_by_section():
    chunks = load_chunks()
    assert len(chunks) > 10
    assert all(c.heading and c.text for c in chunks)


def test_tokenize_drops_stopwords_and_plurals():
    assert tokenize("The moods of songs") == ["mood", "song"]


@pytest.mark.parametrize("query,heading", [
    ("music for studying and deep work", "Studying and deep work"),
    ("what should I play to fall asleep", "Falling asleep and winding down"),
    ("sad heartbroken", "Near-synonyms and how to map them"),
])
def test_retrieval_finds_relevant_section(retriever, query, heading):
    assert heading in [c.heading for c in retriever.search(query, top_k=2)]


def test_retrieval_returns_nothing_for_gibberish(retriever):
    assert retriever.search("zzzz qqqq") == []


def test_search_tool_includes_citations(tools):
    assert "[listening_contexts.md > Studying and deep work]" in tools.search_knowledge("studying")


def test_catalog_options_lists_real_labels(tools):
    options = json.loads(tools.list_catalog_options())
    assert "lofi" in options["genres"] and "chill" in options["moods"]


def test_recommend_tool_scores_and_records_titles(tools):
    out = json.loads(tools.recommend_songs(mood="chill", genre="lofi", energy=0.4, k=3))
    assert len(out["results"]) == 3
    assert out["results"][0]["match_percent"] >= 80
    assert tools.recommended == [r["title"] for r in out["results"]]


def test_recommend_tool_requires_a_preference(tools):
    assert tools.recommend_songs().startswith("Error")


def test_tool_schemas_hide_nothing_required(tools):
    schemas = {t.to_dict()["name"]: t.to_dict()["input_schema"] for t in build_tools(tools)}
    assert set(schemas) == {"search_knowledge", "list_catalog_options", "recommend_songs"}
    assert schemas["search_knowledge"]["required"] == ["query"]
    assert "required" not in schemas["recommend_songs"] or schemas["recommend_songs"]["required"] == []


def test_ungrounded_titles_flags_invented_recommendations():
    result = AgentResult(answer="Try Storm Runner and Library Rain", recommended=["Library Rain"])
    assert result.ungrounded_titles(["Storm Runner", "Library Rain"]) == ["Storm Runner"]


def test_run_agent_executes_tools_and_collects_trace():
    """Fake the API: the runner calls our tools, then returns a final message."""
    def fake_runner_factory(**kwargs):
        tool_by_name = {t.to_dict()["name"]: t for t in kwargs["tools"]}

        class Runner:
            def until_done(self):
                tool_by_name["search_knowledge"](query="studying")
                tool_by_name["recommend_songs"](mood="focused", energy=0.4, k=2)
                return SimpleNamespace(
                    stop_reason="end_turn",
                    content=[SimpleNamespace(type="text", text="Try Focus Flow.")],
                )
        return Runner()

    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(tool_runner=fake_runner_factory)))
    result = run_agent("study music", client=client)

    assert result.answer == "Try Focus Flow."
    assert [c["tool"] for c in result.tool_calls] == ["search_knowledge", "recommend_songs"]
    assert "Focus Flow" in result.recommended
