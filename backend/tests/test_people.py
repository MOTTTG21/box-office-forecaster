from datetime import date

from app.routers.people import _build_filmography


def test_crew_credit_beats_cast_credit_for_same_movie():
    # a director who also appears in the cast of their own film - Directing should win
    credits = {
        "cast": [{"id": 1, "title": "Cameo Movie", "release_date": "2020-01-01", "character": "Himself"}],
        "crew": [{"id": 1, "title": "Cameo Movie", "release_date": "2020-01-01", "job": "Director"}],
    }
    result = _build_filmography(credits)
    assert len(result) == 1
    assert result[0].role == "Director"


def test_director_beats_writer_on_same_film():
    credits = {
        "cast": [],
        "crew": [
            {"id": 1, "title": "Dual Credit", "release_date": "2020-01-01", "job": "Writer"},
            {"id": 1, "title": "Dual Credit", "release_date": "2020-01-01", "job": "Director"},
        ],
    }
    result = _build_filmography(credits)
    assert len(result) == 1
    assert result[0].role == "Director"


def test_ignores_noisy_crew_jobs():
    credits = {"cast": [], "crew": [{"id": 1, "title": "X", "release_date": "2020-01-01", "job": "Thanks"}]}
    assert _build_filmography(credits) == []


def test_skips_credits_missing_release_date():
    credits = {"cast": [{"id": 1, "title": "Unreleased", "release_date": None, "character": "Lead"}], "crew": []}
    assert _build_filmography(credits) == []


def test_cast_credit_uses_character_as_role():
    credits = {"cast": [{"id": 1, "title": "Movie", "release_date": "2020-01-01", "character": "Neo"}], "crew": []}
    result = _build_filmography(credits)
    assert result[0].role == "as Neo"


def test_sorted_most_recent_first():
    credits = {
        "cast": [
            {"id": 1, "title": "Older", "release_date": "2010-01-01", "character": "A"},
            {"id": 2, "title": "Newer", "release_date": "2020-01-01", "character": "B"},
        ],
        "crew": [],
    }
    result = _build_filmography(credits)
    assert [item.tmdb_id for item in result] == [2, 1]
    assert result[0].release_date == date(2020, 1, 1)
