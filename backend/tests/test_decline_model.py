import pytest

from app.ml.decline_model import Transition, collect_transitions, predict_next_weekend_gross


def _obs(week_number: int, weekend_gross_usd: int):
    class _Obs:
        pass

    obs = _Obs()
    obs.week_number = week_number
    obs.weekend_gross_usd = weekend_gross_usd
    return obs


def test_collects_transitions_between_consecutive_weeks():
    by_movie = {1: [_obs(1, 100), _obs(2, 60), _obs(3, 30)]}
    transitions = collect_transitions(by_movie)
    assert len(transitions) == 2
    assert {(t.week_number, t.prior_gross, t.actual_gross) for t in transitions} == {
        (2, 100, 60),
        (3, 60, 30),
    }


def test_skips_gap_weeks_with_no_prior_observation():
    # week 3 has no week-2 row to compare against - shouldn't produce a transition
    by_movie = {1: [_obs(1, 100), _obs(3, 30)]}
    transitions = collect_transitions(by_movie)
    assert transitions == []


def test_skips_missing_gross_values():
    by_movie = {1: [_obs(1, 100), _obs(2, None)]}
    assert collect_transitions(by_movie) == []


def test_predicts_using_median_ratio_of_other_movies_at_same_week():
    transitions = [
        Transition(movie_id=1, week_number=2, prior_gross=100, actual_gross=50),  # ratio 0.5
        Transition(movie_id=2, week_number=2, prior_gross=100, actual_gross=60),  # ratio 0.6
        Transition(movie_id=3, week_number=2, prior_gross=200, actual_gross=90),  # target, excluded from pool
    ]
    predicted = predict_next_weekend_gross(transitions, exclude_movie_id=3, target_week=2, prior_weekend_gross=200)
    # median of [0.5, 0.6] = 0.55 -> 200 * 0.55 = 110
    assert predicted == pytest.approx(110)


def test_excludes_target_movies_own_transition_from_the_ratio_pool():
    # real bug this guards against: a movie's own history leaking into its own prediction
    # would make backtesting meaningless (every prediction would just be "the right answer")
    transitions = [
        Transition(movie_id=1, week_number=2, prior_gross=100, actual_gross=1),  # ratio 0.01, an outlier
    ]
    predicted = predict_next_weekend_gross(transitions, exclude_movie_id=1, target_week=2, prior_weekend_gross=100)
    assert predicted is None  # no other movies at this week once movie 1's own row is excluded


def test_returns_none_with_no_comps_at_that_week():
    assert predict_next_weekend_gross([], exclude_movie_id=1, target_week=5, prior_weekend_gross=100) is None
