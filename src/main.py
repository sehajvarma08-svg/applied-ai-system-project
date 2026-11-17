"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from .recommender import load_songs, recommend_songs  # python -m src.main
except ImportError:
    from recommender import load_songs, recommend_songs  # python src/main.py


WIDTH = 60
MAX_SCORE = 8.0  # see score_song in recommender.py


def print_recommendations(user_prefs: dict, recommendations: list) -> None:
    """Print each recommendation as a readable block: title, score, reasons."""
    prefs = ", ".join(f"{key}={value}" for key, value in user_prefs.items())

    print()
    print("=" * WIDTH)
    print("TOP RECOMMENDATIONS".center(WIDTH))
    print(f"Profile: {prefs}".center(WIDTH))
    print("=" * WIDTH)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        filled = round(score / MAX_SCORE * 20)
        bar = "#" * filled + "-" * (20 - filled)

        print(f"\n#{rank}  {song['title']}  by {song['artist']}")
        print(f"    {song['genre']} / {song['mood']}")
        print(f"    Score: {score:.2f} / {MAX_SCORE:.1f}  [{bar}]")
        print("    Reasons:")
        for reason in explanation.split(", "):
            print(f"      - {reason}")

    print()
    print("=" * WIDTH)


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print_recommendations(user_prefs, recommendations)


if __name__ == "__main__":
    main()
