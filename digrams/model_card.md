# 🎧 Model Card: VibeFinder Agent (Music Recommender with RAG and Tool Use)

## 1. Model Name

**VibeFinder Agent**, built on top of **VibeFinder 2.0** (the original weighted-scoring recommender).

---

## 2. Intended Use

It takes a plain-English request like "something calm to study to on a rainy night" and returns up to 5 songs from a small catalog, each with a reason and a cited source. It is built for classroom exploration, not real listeners. It only recommends songs that exist in the catalog, and it is meant to say so plainly when nothing fits.

Not intended for: production use, catalogs it hasn't been tuned for, or any decision where a wrong recommendation matters.

---

## 3. How the System Works

The system has three parts.

- **Scorer (`src/recommender.py`)** is the source of truth for ranking. Mood match is worth 2.0 and genre match 1.0. Closeness on energy (2.0), valence (1.5), acousticness (1.0) and danceability (0.5) adds the rest. Only features the user asked for count, so the maximum score changes per request. Each song gets a score, a match percentage and a list of reasons.
- **Retriever (`src/rag.py`)** splits the markdown files in `data/knowledge/` (moods, listening contexts, genres and features) into one chunk per `##` section and ranks them with BM25 keyword search. Each result carries a citation like `listening_contexts.md > Studying and deep work`.
- **Agent (`src/agent.py`)** is Claude (`claude-opus-5-5`) with three tools: `search_knowledge`, `list_catalog_options` and `recommend_songs`. It retrieves guidance, maps the request to exact catalog labels and numbers, scores the songs, and retries with adjusted preferences if the best match is under 50% of the maximum. It then answers with reasons and sources.

The language model interprets the request and explains the result. It never ranks songs itself. The original no-LLM CLI (`python -m src.main`) still works without an API key.

---

## 4. Data

- **Catalog:** 20 songs in `data/songs.csv` with genre, mood, energy, tempo, valence, danceability and acousticness. It spans 18 genres and 19 moods, mostly one or two songs per genre. It has no lyrics, language, popularity or listening history.
- **Knowledge base:** three hand-written markdown files in `data/knowledge/`. I wrote them, so they reflect my own views of what "studying music" or "a sad mood" means.
- **`data/TopSongs.csv`:** a larger numeric dataset the scorer can also load, with numeric features scaled to the same range. The agent's tests and examples use `songs.csv`.

---

## 5. Strengths

- Handles fuzzy requests that the original scorer could not, because Claude turns them into catalog labels and numbers.
- Every recommendation can be traced to a score, score reasons and a retrieved source. The match percentage gives the agent (and me) a number for "is this a good answer?"
- Failure is visible: weak matches trigger a retry, and the system prompt tells the agent to admit when the catalog has no good match.
- The tools are plain Python methods, so retrieval and scoring are tested without calling the API.

---

## 6. Limitations and Bias

- **Hand-picked weights.** Mood and genre are all-or-nothing exact matches worth 3 of the possible points. "chill"/"relaxed" and "indie"/"indie pop" count as total mismatches, which can bury good cross-genre songs.
- **Tiny catalog.** With one or two songs per genre, niche requests (for example k-pop, euphoric) get thin results. In a test, the best result scored only 67% on a mood match alone and the rest scored 0.
- **Keyword retrieval.** BM25 matches words, not meaning, so "wind down" will not find a section that only says "relax". Content outside a `##` heading is never indexed.
- **Knowledge base bias.** The guidance reflects one person's opinions and mostly Western genre categories. The agent repeats it with more confidence than it deserves.
- **Friendlier language hides the same biases.** The agent's fluent answers make the scorer's weighting choices easier to miss.
- **Guardrail is weak.** `ungrounded_titles()` only warns, uses substring matching, can false-alarm on titles made of common words, and can miss a paraphrased title.
- **Retry threshold is a judgment call.** The 50% rule costs extra API calls and may retry results that were fine.
- **LLM behavior is not fully controlled.** Claude chooses the tool order and the numbers it passes to the scorer. A different phrasing of the same request can give a different list.
- **No personal data is collected**, but requests are sent to the Anthropic API when the agent runs.

---

## 7. Evaluation

- **Automated tests:** `pytest` runs 57 tests, all passing, in about a second, with no API calls. They cover scoring, ranking, tie-breaking, CSV loading (including header typos and `TopSongs.csv` scaling), chunking, retrieval for sample queries, gibberish returning nothing, tool output and schemas, rejection of an empty preference set, the invented-title detector, and a full `run_agent` run with a mocked client.
- **Scorer examples (run for real):** `pop / happy / energy 0.8` ranked Sunrise City first (4.96 / 5.0). Gym Hero (pop, intense) placed third above better-fitting mood songs, which showed how much genre and energy can outweigh mood. `lofi / chill / energy 0.35 / acousticness 0.8` ranked Library Rain first at 99%.
- **Retrieval:** "studying late at night" returned the "Studying and deep work" section as expected.
- **Not tested:** the live agent. I had no API key while writing this, so tool order, retry behavior and answer quality with the real model are unverified. The agent example in the README is the expected flow from the code and prompt, not a captured run.
- **Lesson from evaluation:** the maximum score depends on which features the user supplies, so scores like 4.96 / 5.0 and 5.94 / 6.0 are not comparable across requests. An early README assumed a fixed maximum of 8.0, which was wrong after the scorer changed.

---

## 8. Future Work

- Run the agent live on a set of test requests and record tool order, retries and failures.
- Add partial credit for related moods and genres, and use tempo as a feature.
- Replace or supplement BM25 with embeddings so paraphrases are found.
- Make the guardrail stricter (block, not just warn) and match titles exactly.
- Use a larger and more varied catalog, and a diversity rule to avoid near-duplicate results.
- Support users with more than one taste.

---

## 9. AI Collaboration and Reflection

**How AI was used.** Claude helped design and write the agent, retriever, tests and documentation. I used the original scorer's behavior as the ground truth to check it against.

**A suggestion that helped.** Keeping the ranking in deterministic code and giving the LLM tools, instead of letting it pick songs directly. It kept the explainability of the original project and made the agent's output checkable.

**A suggestion that was wrong or needed fixing.** The README's early "out of 8.0" score claim was wrong once the scorer only counted requested features. I corrected it to a per-request maximum and re-checked the example scores by running the code.

**Reflection.** The hard part of adding an LLM was deciding what it should not do. The most useful pieces were small deterministic ones: a score the agent can read, citations, a loop cap of 8 rounds and a title check. The hand-picked weights and tiny catalog from the original project are still the main source of bias, and the agent makes them easier to miss, so the honest "no good match" answer is the behavior I most want to keep.

> Note: sections on my own collaboration process (the accepted and rejected suggestions above) should be reviewed and edited to match what actually happened.
