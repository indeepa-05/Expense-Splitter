"""Exact split calculations using integer cents."""


class InvalidEqualSplitError(ValueError):
    """Raised when an equal split cannot be calculated from the inputs."""


def calculate_equal_split(
    total_cents: int,
    participant_ids: list[int],
) -> dict[int, int]:
    """Split positive cents equally, assigning remainder cents in input order."""
    if not isinstance(total_cents, int) or isinstance(total_cents, bool):
        raise InvalidEqualSplitError("Total cents must be an integer")
    if total_cents <= 0:
        raise InvalidEqualSplitError("Total cents must be greater than zero")
    if not participant_ids:
        raise InvalidEqualSplitError("At least one participant is required")
    if any(
        not isinstance(participant_id, int) or isinstance(participant_id, bool)
        for participant_id in participant_ids
    ):
        raise InvalidEqualSplitError("Participant IDs must be integers")
    if len(set(participant_ids)) != len(participant_ids):
        raise InvalidEqualSplitError("Participant IDs must not contain duplicates")

    base_share, remainder = divmod(total_cents, len(participant_ids))
    return {
        participant_id: base_share + (position < remainder)
        for position, participant_id in enumerate(participant_ids)
    }
