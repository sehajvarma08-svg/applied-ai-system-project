# Genres and audio features

## Audio features, in plain language
Energy (0-1) is intensity and loudness. Valence (0-1) is musical positivity: high is cheerful, low is sad or tense. Danceability (0-1) is how steady and rhythmic a track is. Acousticness (0-1) is the likelihood the track is acoustic rather than electronic. Tempo is in BPM; 60-80 is slow, 100-120 moderate, 140+ fast.

## Genre families
Pop and indie pop: bright, hook-driven, high valence. Rock and metal: guitar-driven, high energy, lower valence. Lofi and ambient: low energy, texture-focused, great for background listening. Jazz and classical: acoustic, low-to-mid energy, rich harmony. Synthwave and electronic and edm: synth-based, from moody (synthwave) to euphoric (edm). Hip hop and r&b: vocal and rhythm-forward, medium energy, high danceability. Folk and country: acoustic storytelling, lower energy. Latin and reggae: rhythmic, warm, danceable and laid-back to festive.

## Cross-genre discovery
Genre is only worth 1 point in the scorer, while mood is worth 2 and energy 2. Users who say "I love X" can often be happy with a neighboring genre of the same mood and energy: lofi and ambient, pop and indie pop, rock and metal, electronic and synthwave, jazz and r&b.

## Choosing target numbers
Translate descriptions to numbers: "very chill" is energy 0.3, "mid" is 0.55, "high" is 0.8, "maximum" is 0.95. For acousticness, "acoustic" is 0.8 and "electronic" is 0.2. Only set the fields the request actually implies; leaving a field unset means it is not scored.
