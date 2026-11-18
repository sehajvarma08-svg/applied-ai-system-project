"""Reproducible demo of the deterministic parts + guardrails. Needs no API key.
Run: python scripts_demo.py > logs/guardrail_demo.txt
"""
import json
from src.recommender import load_songs
from src.rag import Retriever
from src.agent import MusicTools, AgentResult, MAX_ITERATIONS

songs = load_songs("data/songs.csv")
t = MusicTools(songs, Retriever.from_directory())
titles = [s["title"] for s in songs]

def show(name, out):
    print(f"\n### {name}\n{out}")

show("A. RAG: in-domain query  search_knowledge('studying late at night', top_k=2)",
     t.search_knowledge("studying late at night", top_k=2))
show("B. RAG guardrail: gibberish query  search_knowledge('zzqx plorf wibble')",
     t.search_knowledge("zzqx plorf wibble"))
show("C. Catalog labels  list_catalog_options()", t.list_catalog_options())
show("D. Scorer: strong match  recommend_songs(lofi, chill, energy=.35, acousticness=.8, k=3)",
     json.dumps([(r["title"], r["match_percent"]) for r in json.loads(
         t.recommend_songs(genre="lofi", mood="chill", energy=0.35, acousticness=0.8, k=3))["results"]]))
weak = json.loads(t.recommend_songs(genre="k-pop", mood="euphoric", k=3))
show("E. Scorer: thin match (only 1 of 3 results scores above 0)  recommend_songs(k-pop, euphoric, k=3)",
     json.dumps([(r["title"], r["match_percent"]) for r in weak["results"]]) +
     f"\nbest match = {weak['results'][0]['match_percent']}% (mood only); results 2-3 are 0%. The 50% retry rule would NOT fire here; the other two are padding.")
show("F. Input guardrail: empty preferences  recommend_songs()", t.recommend_songs())
show("G. Input guardrail: k clamped  recommend_songs(genre='pop', k=999) returns n results",
     len(json.loads(t.recommend_songs(genre="pop", k=999))["results"]))

ok = AgentResult(answer="I picked Library Rain for you.", recommended=["Library Rain"])
bad = AgentResult(answer="Try Library Rain and also Gym Hero.", recommended=["Library Rain"])
show("H. Hallucination guard: grounded answer  ungrounded_titles()", ok.ungrounded_titles(titles))
show("I. Hallucination guard: answer mentions unreturned catalog song", bad.ungrounded_titles(titles))
show("J. Loop cap", f"MAX_ITERATIONS = {MAX_ITERATIONS}")
