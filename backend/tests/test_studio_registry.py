from app.services.studio_registry import all_studios, get_studio, match_studio_slug


def test_matches_a_single_recognized_company():
    assert match_studio_slug([{"id": 33, "name": "Universal Pictures"}]) == "universal"


def test_matches_the_first_recognized_company_in_a_co_production():
    # Marvel Studios (Disney) listed before Columbia Pictures (Sony) - Spider-Man's real shape.
    companies = [
        {"id": 420, "name": "Marvel Studios"},
        {"id": 5, "name": "Columbia Pictures"},
    ]
    assert match_studio_slug(companies) == "disney"


def test_returns_none_when_no_company_is_recognized():
    companies = [{"id": 999999, "name": "Some Indie Financier"}]
    assert match_studio_slug(companies) is None


def test_returns_none_for_an_empty_list():
    assert match_studio_slug([]) is None


def test_get_studio_returns_none_for_unknown_slug():
    assert get_studio("not-a-real-studio") is None


def test_get_studio_returns_the_matching_studio():
    studio = get_studio("disney")
    assert studio is not None
    assert studio.ticker == "DIS"


def test_a_studio_with_no_public_parent_has_a_null_ticker():
    studio = get_studio("a24")
    assert studio is not None
    assert studio.ticker is None


def test_all_studios_have_unique_slugs():
    slugs = [studio.slug for studio in all_studios()]
    assert len(slugs) == len(set(slugs))
