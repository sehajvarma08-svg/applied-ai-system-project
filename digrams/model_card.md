# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 2.0**

---

## 2. Intended Use  

It suggests the top 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It assumes the user can state their taste up front, and it is built for classroom exploration, not real users.

---

## 3. How the Model Works  

Each song gets points for matching the user's favorite mood (+2) and genre (+1), plus points for how close its energy, valence, acousticness, and danceability are to what the user wants. The points are added up (max 8) and the highest-scoring songs are recommended, each with a short explanation of why. I replaced the starter's placeholder logic with this weighted scoring and ranking.

---

## 4. Data  

The catalog has 20 songs in `data/songs.csv`, each with genre, mood, energy, tempo, valence, danceability, and acousticness. It spans 18 genres and 19 moods, but with only one or two songs per genre, and it lacks lyrics, language, artist popularity, and listening history.

---

## 5. Strengths  

It works well for users with a clear genre, mood, and energy preference, like "happy pop at high energy," where Sunrise City ranked first. Every score shows exactly which features contributed, so the results are easy to explain.

---

## 6. Limitations and Bias 

Mood and genre are all-or-nothing matches worth 3 of 8 points, so they can bury good cross-genre songs, and near-synonyms like "chill"/"relaxed" or "indie"/"indie pop" count as total mismatches. The weights are my own guesses, and the tiny catalog means niche genres have only one or two songs, so those users get thin results.

---

## 7. Evaluation  

I tested a pop / happy / energy-0.8 profile and checked that matching songs ranked first and the score breakdowns made sense. Sunrise City won as expected, but Gym Hero (pop, intense) placing third above better-fitting mood songs showed how much genre and energy can outweigh mood.

---

## 8. Future Work  

I would add partial credit for related moods and genres, use tempo as a feature, and add a diversity rule to avoid near-duplicate results. I would also support users with multiple tastes and use a larger catalog.

---

## 9. Personal Reflection  

I learned that a simple weighted scoring rule can produce believable recommendations, but the weights quietly encode my own assumptions about what matters. It made me realize that real music apps make similar hidden design choices that shape what people hear.
