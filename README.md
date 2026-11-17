# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

1. Explain your design in plain language.
### The Plan (from `data_flow.md`)

This is a content-based recommender. It compares each song's attributes to what the user says they like. It works in three stages: **Input → Process → Output**.

```mermaid
flowchart TD
    A["INPUT: User Prefs<br/>genre, mood, energy, valence,<br/>acousticness, danceability"] --> B["load_songs(data/songs.csv)<br/>list of song dicts"]
    B --> C{"PROCESS: The Loop<br/>for each song in songs"}
    C --> D["score_song(user_prefs, song)"]
    D --> E["Categorical matches<br/>+2.0 mood match<br/>+1.0 genre match"]
    D --> F["Numeric closeness<br/>closeness = 1 - abs(pref - song value)<br/>2.0 energy, 1.5 valence,<br/>1.0 acousticness, 0.5 danceability"]
    E --> G["total score + reasons list"]
    F --> G
    G --> H["append (song, score, explanation)"]
    H --> C
    C -->|all songs judged| I["OUTPUT: The Ranking<br/>sort by score, descending"]
    I --> J["slice top K"]
    J --> K["Top K Recommendations<br/>(song, score, explanation)"]

1b. Some Possible biases: 
Weighting biases

a. Mood and genre dominate. Mood (+2.0) and genre (+1.0) are all-or-nothing, so they make up 3 of the 8 possible points. A song with the right mood and genre but poor numeric fit can beat a song that is a near-perfect numeric match in a different genre. This can trap users in one genre and hide good cross-genre songs.

b. Weights are the designer's guesses. Energy at 2.0 and danceability at 0.5 reflect my assumptions about what matters. They aren't learned from listener behavior, so they may suit some users and not others.

c. Exact string matching. "chill" and "relaxed" count as a total mismatch, and so do "indie" and "indie pop". Labels that are close in meaning are punished as hard as unrelated ones
``
2. Some prompts to answer:

- What features does each `Song` use in your system?
Ans) The features that each song uses in my system would be 
skips, replays, watch time, saves, playlist 
adds, searches, time of day, and device
- What information does your `UserProfile` store?
Ans) The user profile stores favorite genre, favoite mode, target energy and likes acoustic. 
- How does your `Recommender` compute a score for each song
Ans)It takes the scores for every song in the catalog, sorts them, and keeps the top k(The score for the songs)
- How do you choose which songs to recommend
Ans) It is a combination of the scoring and ranking system. The scoring system scores each song based on certian attributes and the ranking system ranks these song based on their scores. This then help the system recommend songs to a user. 


---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:
## Sample Recommendation Output ##
============================================================
                    TOP RECOMMENDATIONS                     
         Profile: genre=pop, mood=happy, energy=0.8         
============================================================

#1  Sunrise City  by Neon Echo
    pop / happy
    Score: 4.96 / 8.0  [############--------]
    Reasons:
      - mood match (+2.0)
      - genre match (+1.0)
      - energy close (+1.96)

#2  Rooftop Lights  by Indigo Parade
    indie pop / happy
    Score: 3.92 / 8.0  [##########----------]
    Reasons:
      - mood match (+2.0)
      - energy close (+1.92)

#3  Gym Hero  by Max Pulse
    pop / intense
    Score: 2.74 / 8.0  [#######-------------]
    Reasons:
      - genre match (+1.0)
      - energy close (+1.74)

#4  Concrete Psalms  by Verse Theory
    hip hop / confident
    Score: 1.96 / 8.0  [#####---------------]
    Reasons:
      - energy close (+1.96)

#5  Carnaval Nights  by Luz Moreira
    latin / festive
    Score: 1.92 / 8.0  [#####---------------]
    Reasons:
      - energy close (+1.92)


```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

These are reasoned from the scoring rule and the sample output above, not from separate re-runs.

- **Genre weight 1.0 → 0.5:** Genre matters less, so "Gym Hero" (pop / intense) drops further. Cross-genre songs with a good energy fit, like "Rooftop Lights" (indie pop), move up.
- **Adding valence to the score:** Songs with the right mood but the wrong emotional tone get pushed down. This separates songs that share a mood label but feel different.
- **Different users:** A user who matches the catalog's labels (pop / happy) gets clear results. A user with a rare genre or mood gets rankings driven almost entirely by energy, because the exact matches never fire.

---

## Limitations and Risks

- The catalog is tiny, so there are few good matches per user.
- Mood and genre are exact string matches. "indie" vs "indie pop" counts as a total miss.
- Weights are hand-picked guesses, not learned from real listening behavior.
- It ignores lyrics, language, and artist, and has no listening history.
- It can over-favor one genre or mood and hide good cross-genre songs.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Recommenders turn data into predictions by scoring each item against a user profile and ranking the scores. Even a simple weighted sum gives sensible results, and listing the reasons for each score makes the output easy to explain and debug.

Bias comes in through the design choices: which features count, how much each is weighted, and how rigid the matching is. Heavy genre and mood weights can trap users in one style. A small catalog and exact label matching can leave out users whose tastes don't fit the labels.



