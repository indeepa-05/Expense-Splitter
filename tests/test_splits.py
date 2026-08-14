"""Tests for deterministic, exact equal splitting."""

import pytest

from app.services.splits import InvalidEqualSplitError, calculate_equal_split


def test_equal_split_single_person() -> None:
    assert calculate_equal_split(12345, [7]) == {7: 12345}


def test_equal_split_even_amount() -> None:
    assert calculate_equal_split(1200, [1, 2, 3]) == {1: 400, 2: 400, 3: 400}


def test_equal_split_with_remainder() -> None:
    assert calculate_equal_split(10001, [1, 2, 3, 4]) == {
        1: 2501,
        2: 2500,
        3: 2500,
        4: 2500,
    }


def test_equal_split_100_rupees_three_people() -> None:
    shares = calculate_equal_split(10000, [1, 2, 3])

    assert shares == {1: 3334, 2: 3333, 3: 3333}
    assert sum(shares.values()) == 10000


def test_equal_split_large_amount() -> None:
    shares = calculate_equal_split(1200050, [10, 20, 30])

    assert shares == {10: 400017, 20: 400017, 30: 400016}


def test_equal_split_preserves_participant_order_for_remainder() -> None:
    assert calculate_equal_split(10, [30, 10, 20]) == {
        30: 4,
        10: 3,
        20: 3,
    }


def test_equal_split_shares_sum_exactly_to_total() -> None:
    shares = calculate_equal_split(98765, [5, 8, 13, 21, 34, 55])

    assert sum(shares.values()) == 98765


def test_equal_split_empty_participants_rejected() -> None:
    with pytest.raises(InvalidEqualSplitError):
        calculate_equal_split(100, [])


def test_equal_split_duplicate_participants_rejected() -> None:
    with pytest.raises(InvalidEqualSplitError):
        calculate_equal_split(100, [1, 2, 1])


@pytest.mark.parametrize("total_cents", [0, -1, -10000])
def test_non_positive_equal_split_total_rejected(total_cents: int) -> None:
    with pytest.raises(InvalidEqualSplitError):
        calculate_equal_split(total_cents, [1, 2])


def test_equal_split_rounding_invariants_over_many_values() -> None:
    for total_cents in range(1, 3001):
        for participant_count in range(1, 21):
            participant_ids = list(range(1, participant_count + 1))
            shares = calculate_equal_split(total_cents, participant_ids)
            share_values = list(shares.values())

            assert sum(share_values) == total_cents
            assert max(share_values) - min(share_values) <= 1
