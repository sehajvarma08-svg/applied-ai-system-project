"""
Agentic layer for the music recommender.

Claude gets three tools and decides for itself how to use them:
  search_knowledge     RAG: look up mood/genre/context guidance in data/knowledge/
  list_catalog_options which genres and moods the catalog really contains
  recommend_songs      the existing scorer (score_song / recommend_songs)

Typical run: read the request -> retrieve guidance -> map it onto catalog
labels -> score songs -> check the match quality -> retry with adjusted
preferences if it is weak -> answer, citing the guidance it used.

Run:  python -m src.agent "something to study to on a rainy night"
Needs ANTHROPIC_API_KEY (or `ant auth login`) and `pip install anthropic`.
"""

import argparse
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from .rag import Retriever
    from .recommender import load_songs, recommend_songs, max_score
except ImportError:  # python src/agent.py
    from rag import Retriever
    from recommender import load_songs, recommend_songs, max_score

MODEL = "claude-opus-5-5"
DEFAULT_CSV = "data/songs.csv"
MAX_ITERATIONS = 8   # hard cap on tool-use rounds so the agent cannot loop forever
WEAK_MATCH = 0.5     # top score below this share of the maximum triggers a retry

SYSTEM_PROMPT = f"""You are a music recommendation agent for a small fixed catalog.

You can only recommend songs that recommend_songs returns. Never invent songs.

Work like this:
1. Call search_knowledge for guidance on the user's mood, activity or genre.
2. Call list_catalog_options so your mood and genre values are exact catalog labels.
3. Call recommend_songs with only the preferences the request implies.
4. Check the result. If the top song scores under {int(WEAK_MATCH * 100)}% of the maximum, adjust the
   preferences using the guidance (for example a neighboring genre, or drop an
   over-constraining field) and call recommend_songs again.
5. Answer in a short list. For each song say why it fits, using the score reasons,
   and name the knowledge sources ("file > section") that shaped your choices.
   If the catalog has no good match, say so plainly."""


@dataclass
class AgentResult:
    answer: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # trace of what the agent did
    recommended: List[str] = field(default_factory=list)            # titles returned by the scorer

    def ungrounded_titles(self, all_titles: List[str]) -> List[str]:
        """Titles from the catalog that appear in the answer but were never recommended."""
        text = self.answer.lower()
        return [t for t in all_titles if t.lower() in text and t not in self.recommended]


class MusicTools:
    """The agent's tools. Plain methods, so they can be tested without calling the API."""

    def __init__(self, songs: List[Dict], retriever: Retriever):
        self.songs = songs
        self.retriever = retriever
        self.calls: List[Dict[str, Any]] = []
        self.recommended: List[str] = []

    def search_knowledge(self, query: str, top_k: int = 3) -> str:
        chunks = self.retriever.search(query, top_k=max(1, min(top_k, 5)))
        if not chunks:
            return "No relevant guidance found."
        return "\n\n".join(f"[{c.citation}]\n{c.text}" for c in chunks)

    def list_catalog_options(self) -> str:
        def values(key):
            return sorted({str(s[key]) for s in self.songs if key in s})
        return json.dumps({"genres": values("genre"), "moods": values("mood"), "song_count": len(self.songs)})

    def recommend_songs(self, genre: Optional[str] = None, mood: Optional[str] = None,
                        energy: Optional[float] = None, valence: Optional[float] = None,
                        acousticness: Optional[float] = None, danceability: Optional[float] = None,
                        k: int = 5) -> str:
        prefs = {key: value for key, value in {
            "genre": genre, "mood": mood, "energy": energy, "valence": valence,
            "acousticness": acousticness, "danceability": danceability,
        }.items() if value is not None}
        if not prefs:
            return "Error: give at least one preference."

        top = max_score(prefs, self.songs)
        results = recommend_songs(prefs, self.songs, k=max(1, min(k, 10)))
        self.recommended.extend(s["title"] for s, _, _ in results)
        return json.dumps({
            "preferences_used": prefs,
            "max_possible_score": top,
            "results": [
                {"title": s["title"], "artist": s["artist"], "genre": s.get("genre"),
                 "mood": s.get("mood"), "score": round(score, 2),
                 "match_percent": round(100 * score / top) if top else 0, "reasons": why}
                for s, score, why in results
            ],
        })


def build_tools(tools: MusicTools):
    """Wrap MusicTools methods as SDK tools (schemas come from the signatures and docstrings)."""
    from anthropic import beta_tool

    def traced(name, fn):
        def run(**kwargs):
            output = fn(**kwargs)
            tools.calls.append({"tool": name, "input": kwargs, "output": output})
            return output
        return run

    @beta_tool
    def search_knowledge(query: str, top_k: int = 3) -> str:
        """Search the music knowledge base for guidance on moods, genres, activities and audio features.

        Args:
            query: What to look up, e.g. "studying late at night" or "melancholic vs nostalgic".
            top_k: How many passages to return (1-5).
        """
        return traced("search_knowledge", tools.search_knowledge)(query=query, top_k=top_k)

    @beta_tool
    def list_catalog_options() -> str:
        """List the exact genre and mood labels that exist in the song catalog."""
        return traced("list_catalog_options", tools.list_catalog_options)()

    @beta_tool
    def recommend_songs(genre: Optional[str] = None, mood: Optional[str] = None,
                        energy: Optional[float] = None, valence: Optional[float] = None,
                        acousticness: Optional[float] = None, danceability: Optional[float] = None,
                        k: int = 5) -> str:
        """Score every catalog song against the given preferences and return the top k with reasons.

        Only pass fields the request implies; unset fields are not scored. Genre and mood must be
        exact catalog labels (see list_catalog_options). Numeric fields are 0.0-1.0.

        Args:
            genre: Catalog genre label.
            mood: Catalog mood label.
            energy: Target energy, 0.0 (calm) to 1.0 (intense).
            valence: Target positivity, 0.0 (sad) to 1.0 (cheerful).
            acousticness: Target acousticness, 0.0 (electronic) to 1.0 (acoustic).
            danceability: Target danceability, 0.0 to 1.0.
            k: Number of songs to return (1-10).
        """
        return traced("recommend_songs", tools.recommend_songs)(
            genre=genre, mood=mood, energy=energy, valence=valence,
            acousticness=acousticness, danceability=danceability, k=k)

    return [search_knowledge, list_catalog_options, recommend_songs]


def run_agent(request: str, csv_path: str = DEFAULT_CSV, client=None, model: str = MODEL) -> AgentResult:
    """Run the agent on one natural-language request and return its answer plus a trace."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic()

    songs = load_songs(csv_path)
    if not songs:
        raise SystemExit(f"No songs found in {csv_path}")

    tools = MusicTools(songs, Retriever.from_directory())
    runner = client.beta.messages.tool_runner(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        tools=build_tools(tools),
        max_iterations=MAX_ITERATIONS,
        messages=[{"role": "user", "content": request}],
    )
    final = runner.until_done()

    answer = "".join(b.text for b in final.content if b.type == "text").strip()
    if final.stop_reason == "refusal":
        answer = answer or "The request was declined."
    elif final.stop_reason not in ("end_turn", "stop_sequence"):
        answer = (answer + f"\n\n(Stopped early: {final.stop_reason})").strip()

    return AgentResult(answer=answer, tool_calls=tools.calls, recommended=list(dict.fromkeys(tools.recommended)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic music recommender (RAG + tool use)")
    parser.add_argument("request", help='e.g. "upbeat songs for a morning run"')
    parser.add_argument("--csv", default=DEFAULT_CSV, help=f"songs CSV (default: {DEFAULT_CSV})")
    parser.add_argument("--trace", action="store_true", help="print each tool call the agent made")
    args = parser.parse_args()

    result = run_agent(args.request, csv_path=args.csv)

    if args.trace:
        print("\n--- agent trace ---")
        for i, call in enumerate(result.tool_calls, 1):
            print(f"{i}. {call['tool']}({json.dumps(call['input'])})")
    print("\n" + result.answer)

    invented = result.ungrounded_titles([s["title"] for s in load_songs(args.csv)])
    if invented:
        print(f"\nWarning: answer mentions songs the scorer never returned: {', '.join(invented)}")


if __name__ == "__main__":
    main()
