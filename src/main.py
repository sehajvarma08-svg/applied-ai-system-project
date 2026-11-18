"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import argparse

try:
    from .recommender import load_songs, recommend_songs, max_score  # python -m src.main
except ImportError:
    from recommender import load_songs, recommend_songs, max_score  # python src/main.py


WIDTH = 60
DEFAULT_CSV = "data/songs.csv"


def print_recommendations(user_prefs: dict, recommendations: list, top_score: float) -> None:
    """Print each recommendation as a readable block: title, score, reasons."""
    prefs = ", ".join(f"{key}={value}" for key, value in user_prefs.items())

    print()
    print("=" * WIDTH)
    print("TOP RECOMMENDATIONS".center(WIDTH))
    print(f"Profile: {prefs}".center(WIDTH))
    print("=" * WIDTH)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        filled = round(score / top_score * 20) if top_score else 0
        bar = "#" * filled + "-" * (20 - filled)

        print(f"\n#{rank}  {song['title']}  by {song['artist']}")
        details = [f"{f}={song[f]}" for f in ("genre", "mood", "year") if f in song]
        if details:
            print(f"    {' / '.join(details)}")
        print(f"    Score: {score:.2f} / {top_score:.1f}  [{bar}]")
        print("    Reasons:")
        for reason in explanation.split("; "):
            print(f"      - {reason}")

    print()
    print("=" * WIDTH)


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("csv_path", nargs="?", default=DEFAULT_CSV,
                        help=f"path to the songs CSV (default: {DEFAULT_CSV})")
    args = parser.parse_args()

    songs = load_songs(args.csv_path)
    if not songs:
        raise SystemExit(f"No songs found in {args.csv_path}")

    # Starter example profile; TopSongs.csv has numeric moods and no genre/energy.
    if any("genre" in s for s in songs):
        user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    else:
        user_prefs = {"year": 1990, "danceability": 20, "mood": 10, "acousticness": 1}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print_recommendations(user_prefs, recommendations, max_score(user_prefs, songs))


if __name__ == "__main__":
    main()
