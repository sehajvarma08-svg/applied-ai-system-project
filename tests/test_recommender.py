from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""
#''''''''''''''''''''''''''''''''''''''''''



# ---------------------------------------------------------------------------
# Extended tests: loading, scoring, ranking, Recommender, and main helpers
# ---------------------------------------------------------------------------
import pytest

from src.recommender import (
    WEIGHTS,
    _convert,
    _is_number,
    _norm,
    compute_spans,
    load_songs,
    max_score,
    recommend_songs,
    score_song,
)
from src import main as main_module


def write_csv(tmp_path, text, name="songs.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


SONGS = [
    {"id": 1, "title": "Pop Hit", "artist": "A", "genre": "pop", "mood": "happy", "energy": 0.8},
    {"id": 2, "title": "Lofi Loop", "artist": "B", "genre": "lofi", "mood": "chill", "energy": 0.3},
    {"id": 3, "title": "Rock Anthem", "artist": "C", "genre": "rock", "mood": "intense", "energy": 0.95},
]


# ---- helpers --------------------------------------------------------------

def test_is_number():
    assert _is_number(1) and _is_number(1.5)
    assert not _is_number(True)
    assert not _is_number("1")
    assert not _is_number(None)


def test_norm_is_case_and_separator_insensitive():
    assert _norm("Hip-Hop") == _norm("hip hop") == _norm("  HIP_HOP ")


def test_convert_types():
    assert _convert("title", " 123 ") == "123"          # text stays text, stripped
    assert _convert("year", "1990.0") == 1990           # int field
    assert isinstance(_convert("id", "7"), int)
    assert _convert("energy", "0.5") == 0.5
    assert _convert("mood", "happy") == "happy"         # non-numeric falls back to str
    assert _convert("mood", "10.5") == 10.5             # numeric mood (TopSongs)


# ---- load_songs -----------------------------------------------------------

def test_load_songs_converts_and_fixes_typos(tmp_path):
    path = write_csv(
        tmp_path,
        "id,title,artist,year,dancbility,mood,valance\n"
        "1,Song A,Artist,1990,39.9,happy,2.5\n",
    )
    songs = load_songs(path)
    assert len(songs) == 1
    s = songs[0]
    assert s["danceability"] == 39.9 and "dancbility" not in s
    assert s["valence"] == 2.5 and "valance" not in s
    assert s["year"] == 1990 and isinstance(s["year"], int)
    assert s["mood"] == "happy"


def test_load_songs_skips_blank_columns(tmp_path):
    path = write_csv(tmp_path, "id,title,,energy\n1,A,junk,0.5\n")
    song = load_songs(path)[0]
    assert "" not in song and song["energy"] == 0.5


def test_load_songs_real_data_files():
    songs = load_songs("data/songs.csv")
    assert songs and {"title", "genre", "mood", "energy"} <= set(songs[0])


def test_load_songs_empty_file_returns_empty_list(tmp_path):
    assert load_songs(write_csv(tmp_path, "id,title\n")) == []


# ---- compute_spans / max_score -------------------------------------------

def test_compute_spans_floor_is_one():
    spans = compute_spans([{"energy": 0.1}, {"energy": 0.9}])
    assert spans["energy"] == 1.0


def test_compute_spans_wide_range():
    spans = compute_spans([{"year": 1901}, {"year": 2014}])
    assert spans["year"] == 113


def test_compute_spans_ignores_text_and_missing():
    spans = compute_spans([{"mood": "happy"}, {"energy": 0.5}])
    assert "mood" not in spans


def test_max_score_sums_requested_features():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    assert max_score(prefs, SONGS) == WEIGHTS["genre"] + WEIGHTS["mood"] + WEIGHTS["energy"]


def test_max_score_accepts_single_song_dict():
    assert max_score({"genre": "pop"}, SONGS[0]) == WEIGHTS["genre"]


def test_max_score_ignores_features_no_song_has():
    assert max_score({"genre": "pop", "year": 1990}, SONGS) == WEIGHTS["genre"]


def test_max_score_uses_any_song_not_just_first():
    songs = [{"title": "x"}, {"title": "y", "energy": 0.5}]
    assert max_score({"energy": 0.5}, songs) == WEIGHTS["energy"]


# ---- score_song -----------------------------------------------------------

def test_score_exact_match_is_max():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    score, reasons = score_song(prefs, SONGS[0])
    assert score == pytest.approx(max_score(prefs, SONGS))
    assert any("genre match" in r for r in reasons)


def test_score_text_match_is_case_insensitive():
    score, _ = score_song({"genre": "POP"}, {"genre": "pop"})
    assert score == WEIGHTS["genre"]


def test_score_text_mismatch_earns_nothing():
    score, reasons = score_song({"genre": "pop"}, {"genre": "rock"})
    assert score == 0 and reasons == []


def test_score_numeric_closeness_is_linear():
    score, _ = score_song({"energy": 0.5}, {"energy": 0.7})
    assert score == pytest.approx(WEIGHTS["energy"] * 0.8)


def test_score_numeric_never_negative():
    score, reasons = score_song({"energy": 0.0}, {"energy": 50.0})
    assert score == 0
    assert "far" in reasons[0] and "(+0.00)" in reasons[0]


def test_score_reason_labels():
    _, close = score_song({"energy": 0.5}, {"energy": 0.55})
    _, off = score_song({"energy": 0.5}, {"energy": 0.9})
    assert "close" in close[0] and "off" in off[0]


def test_score_number_vs_text_is_incomparable():
    score, reasons = score_song({"mood": 10}, {"mood": "happy"})
    assert score == 0 and reasons == []
    score, reasons = score_song({"mood": "happy"}, {"mood": 10})
    assert score == 0 and reasons == []


def test_score_skips_features_missing_from_song_or_prefs():
    assert score_song({"energy": 0.5}, {"genre": "pop"}) == (0.0, [])
    assert score_song({}, {"energy": 0.5}) == (0.0, [])


def test_score_ignores_unweighted_keys():
    score, _ = score_song({"tempo_bpm": 120}, {"tempo_bpm": 120})
    assert score == 0


def test_score_uses_spans_to_scale():
    # 10-year gap over a 100-year span -> 90% of year weight
    score, _ = score_song({"year": 1990}, {"year": 2000}, {"year": 100.0})
    assert score == pytest.approx(WEIGHTS["year"] * 0.9)


def test_score_bool_not_treated_as_number():
    score, _ = score_song({"genre": True}, {"genre": True})
    assert score == WEIGHTS["genre"]


# ---- recommend_songs ------------------------------------------------------

def test_recommend_songs_ranks_best_first():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    results = recommend_songs(prefs, SONGS, k=3)
    assert [r[0]["title"] for r in results][0] == "Pop Hit"
    scores = [r[1] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_songs_respects_k():
    assert len(recommend_songs({"energy": 0.5}, SONGS, k=2)) == 2
    assert len(recommend_songs({"energy": 0.5}, SONGS, k=10)) == len(SONGS)


def test_recommend_songs_result_shape():
    song, score, explanation = recommend_songs({"genre": "pop"}, SONGS, k=1)[0]
    assert isinstance(song, dict) and isinstance(score, float) and isinstance(explanation, str)


def test_recommend_songs_no_matching_features_message():
    _, _, explanation = recommend_songs({"genre": "jazz"}, SONGS, k=1)[0]
    assert explanation == "no matching features"


def test_recommend_songs_ties_broken_by_title():
    songs = [{"title": "Zebra", "genre": "pop"}, {"title": "Apple", "genre": "pop"}]
    results = recommend_songs({"genre": "pop"}, songs, k=2)
    assert [r[0]["title"] for r in results] == ["Apple", "Zebra"]


def test_recommend_songs_empty_list():
    assert recommend_songs({"genre": "pop"}, [], k=5) == []


def test_recommend_songs_explanation_joined_with_semicolons():
    _, _, explanation = recommend_songs({"genre": "pop", "mood": "happy"}, SONGS, k=1)[0]
    assert "; " in explanation


# ---- Recommender class ----------------------------------------------------

def make_user(**overrides):
    base = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=False)
    base.update(overrides)
    return UserProfile(**base)


def test_recommender_respects_k():
    rec = make_small_recommender()
    assert len(rec.recommend(make_user(), k=1)) == 1


def test_recommender_ranks_by_user_preferences():
    rec = make_small_recommender()
    chill_user = make_user(favorite_genre="lofi", favorite_mood="chill", target_energy=0.4, likes_acoustic=True)
    assert rec.recommend(chill_user, k=2)[0].genre == "lofi"
    assert rec.recommend(make_user(), k=2)[0].genre == "pop"


def test_recommender_likes_acoustic_changes_ranking():
    rec = make_small_recommender()
    # Neutral genre/mood/energy so acousticness decides.
    acoustic = make_user(favorite_genre="x", favorite_mood="x", target_energy=0.6, likes_acoustic=True)
    non_acoustic = make_user(favorite_genre="x", favorite_mood="x", target_energy=0.6, likes_acoustic=False)
    assert rec.recommend(acoustic, k=1)[0].genre == "lofi"
    assert rec.recommend(non_acoustic, k=1)[0].genre == "pop"


def test_recommender_does_not_mutate_songs():
    rec = make_small_recommender()
    before = list(rec.songs)
    rec.recommend(make_user(), k=2)
    assert rec.songs == before


def test_recommender_explanation_mentions_score_and_reasons():
    rec = make_small_recommender()
    text = rec.explain_recommendation(make_user(), rec.songs[0])
    assert text.startswith("Score ")
    assert "genre match" in text and "mood match" in text


def test_recommender_explanation_when_nothing_matches_is_still_nonempty():
    rec = make_small_recommender()
    user = make_user(favorite_genre="jazz", favorite_mood="sad", target_energy=50.0, likes_acoustic=False)
    assert rec.explain_recommendation(user, rec.songs[1]).strip() != ""


# ---- main.py --------------------------------------------------------------

def test_print_recommendations_output(capsys):
    prefs = {"genre": "pop", "mood": "happy"}
    recs = recommend_songs(prefs, SONGS, k=2)
    main_module.print_recommendations(prefs, recs, max_score(prefs, SONGS))
    out = capsys.readouterr().out
    assert "TOP RECOMMENDATIONS" in out
    assert "Pop Hit" in out and "Reasons:" in out and "genre match" in out


def test_print_recommendations_zero_top_score_does_not_crash(capsys):
    recs = recommend_songs({"genre": "jazz"}, SONGS, k=1)
    main_module.print_recommendations({"genre": "jazz"}, recs, 0)
    assert "no matching features" in capsys.readouterr().out


def test_main_runs_on_default_csv(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["main", "data/songs.csv"])
    main_module.main()
    assert "TOP RECOMMENDATIONS" in capsys.readouterr().out


def test_main_exits_on_empty_csv(monkeypatch, tmp_path):
    path = write_csv(tmp_path, "id,title\n")
    monkeypatch.setattr("sys.argv", ["main", path])
    with pytest.raises(SystemExit):
        main_module.main()
