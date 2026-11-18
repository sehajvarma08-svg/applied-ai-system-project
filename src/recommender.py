import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    @staticmethod
    def _prefs(user: UserProfile) -> Dict:
        return {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "acousticness": 0.8 if user.likes_acoustic else 0.2,
        }

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        spans = compute_spans([asdict(s) for s in self.songs])
        return score_song(self._prefs(user), asdict(song), spans)

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        spans = compute_spans([asdict(s) for s in self.songs])
        prefs = self._prefs(user)
        ranked = sorted(
            self.songs,
            key=lambda s: (-score_song(prefs, asdict(s), spans)[0], s.title),
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        score, reasons = self._score(user, song)
        return f"Score {score:.2f}: " + ("; ".join(reasons) or "no matching features")

# One weight per feature. A feature only counts when it is in both the user's
# prefs and the song, so the same code works for songs.csv and TopSongs.csv.
# Text values (e.g. mood="happy") score by exact match; numeric values by closeness.
WEIGHTS = {
    "mood": 2.0,
    "genre": 1.0,
    "energy": 2.0,
    "valence": 1.5,
    "acousticness": 1.0,
    "danceability": 0.5,
    "year": 1.0,
}

# Some CSV headers have typos; map them to the canonical names.
COLUMN_ALIASES = {"dancbility": "danceability", "valance": "valence"}
INT_FIELDS = {"id", "year"}
TEXT_FIELDS = {"title", "artist", "genre"}


def _convert(field: str, value: str):
    """Convert a CSV cell: ints for id/year, text for names, else float if possible."""
    value = value.strip()
    if field in TEXT_FIELDS:
        return value
    if field in INT_FIELDS:
        return int(float(value))
    try:
        return float(value)
    except ValueError:
        return value  # e.g. mood="happy"


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file into dicts, fixing header typos and converting numbers."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            song = {}
            for key, value in row.items():
                if key is None or not key.strip() or value is None:
                    continue  # skip blank/extra columns
                name = COLUMN_ALIASES.get(key.strip(), key.strip())
                song[name] = _convert(name, value)
            songs.append(song)
    return songs


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _norm(value) -> str:
    """Normalize text for matching: case-insensitive, '-'/'_' treated as spaces."""
    return " ".join(str(value).lower().replace("-", " ").replace("_", " ").split())


def compute_spans(songs: List[Dict]) -> Dict[str, float]:
    """Per-feature value range, never below 1.0, used to scale numeric differences.

    songs.csv features are already 0-1 so their span stays 1.0 (unchanged scoring);
    TopSongs.csv features span 0-40 or 1901-2014, so they get scaled down to 0-1.
    """
    spans: Dict[str, float] = {}
    for feature in WEIGHTS:
        values = [s[feature] for s in songs if _is_number(s.get(feature))]
        if values:
            spans[feature] = max(1.0, max(values) - min(values))
    return spans


def max_score(user_prefs: Dict, songs) -> float:
    """Highest score this profile can earn on the dataset.

    `songs` may be one song dict or a list; a feature counts if the user asked
    for it and at least one song has it.
    """
    if isinstance(songs, dict):
        songs = [songs]
    return sum(
        w for f, w in WEIGHTS.items()
        if f in user_prefs and any(f in s for s in songs)
    )


def score_song(user_prefs: Dict, song: Dict, spans: Optional[Dict[str, float]] = None) -> Tuple[float, List[str]]:
    """Score one song against user preferences, returning (score, reasons)."""
    spans = spans or {}
    score = 0.0
    reasons: List[str] = []

    for feature, weight in WEIGHTS.items():
        if feature not in user_prefs or feature not in song:
            continue
        wanted, actual = user_prefs[feature], song[feature]
        if _is_number(wanted) and _is_number(actual):
            diff = abs(wanted - actual) / spans.get(feature, 1.0)
            points = weight * max(0.0, 1 - diff)
            score += points
            label = "close" if diff < 0.25 else "far" if diff >= 1 else "off"
            reasons.append(f"{feature} {label} (+{points:.2f})")
        elif not _is_number(wanted) and not _is_number(actual):
            if _norm(wanted) == _norm(actual):
                score += weight
                reasons.append(f"{feature} match (+{weight:.1f})")
        # number vs text: incomparable, earns nothing

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Return the top-k songs as (song, score, explanation), ranked by score.

    Ties are broken alphabetically by title so results are deterministic.
    """
    spans = compute_spans(songs)
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, spans)
        scored.append((song, score, "; ".join(reasons) or "no matching features"))
    scored.sort(key=lambda item: (-item[1], str(item[0].get("title", ""))))
    return scored[:k]
