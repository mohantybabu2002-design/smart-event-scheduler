"""
Overlap-detection logic.

Kept separate from the API routes on purpose: this is the "algorithm"
part of the project, and keeping it isolated makes it easy to (a)
test in isolation, and (b) point to directly in an interview.

THE CORE RULE (classic interval-overlap check):
Two time ranges [startA, endA) and [startB, endB) overlap if:
    startA < endB AND startB < endA

Why this formula and not something more complicated?
Think of it as: they DON'T overlap if one ends before the other
starts (endA <= startB) OR the other ends before this one starts
(endB <= startA). Overlap is just the negation of that.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List
from app import models


def ranges_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    """Pure function, no DB -- easy to unit test on its own."""
    return start_a < end_b and start_b < end_a


def get_conflicting_events(
    db: Session,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_event_id: int = None,
) -> List[models.Event]:
    """
    Finds existing events that would conflict with a NEW event
    for this user, whether they're the host OR a participant.

    This is the query-based version of the same overlap rule above,
    translated into SQL: instead of checking one pair of times in
    Python, we ask the database "give me every event this user is
    part of where existing.start < new.end AND new.start < existing.end".
    """
    query = (
        db.query(models.Event)
        .outerjoin(models.Participant, models.Participant.event_id == models.Event.id)
        .filter(
            or_(
                models.Event.host_id == user_id,
                models.Participant.user_id == user_id,
            ),
            # the overlap condition, applied inside SQL
            and_(
                models.Event.start_time < end_time,
                models.Event.end_time > start_time,
            ),
        )
    )

    if exclude_event_id is not None:
        # needed when checking an UPDATE to an existing event --
        # otherwise the event would "conflict with itself"
        query = query.filter(models.Event.id != exclude_event_id)

    return query.distinct().all()


def get_busy_intervals(
    db: Session, user_ids: List[int], range_start: datetime, range_end: datetime
) -> List[tuple]:
    """
    Returns every (start, end) time this GROUP of users is busy,
    within the given range -- as host OR participant, for any of them.
    """
    events = (
        db.query(models.Event)
        .outerjoin(models.Participant, models.Participant.event_id == models.Event.id)
        .filter(
            or_(
                models.Event.host_id.in_(user_ids),
                models.Participant.user_id.in_(user_ids),
            ),
            models.Event.start_time < range_end,
            models.Event.end_time > range_start,
        )
        .distinct()
        .all()
    )
    return [(e.start_time, e.end_time) for e in events]


def merge_intervals(intervals: List[tuple]) -> List[tuple]:
    """
    Classic 'merge overlapping intervals' problem.

    Sort by start time, then walk through: if the next interval starts
    before (or exactly when) the current one ends, they overlap or
    touch -- merge them into one by extending the end time. Otherwise,
    the current interval is finished; start a new one.
    """
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_intervals[0]]

    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:  # overlaps or touches the previous merged interval
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def find_common_free_slots(
    db: Session,
    user_ids: List[int],
    range_start: datetime,
    range_end: datetime,
    min_duration_minutes: int = 30,
) -> List[tuple]:
    """
    THE feature: "when can all these people meet?"

    Approach:
    1. Collect every busy interval for ANY of these users (if even one
       person is busy, the group can't meet then).
    2. Merge overlapping busy intervals into a clean, non-overlapping list.
    3. Walk through the gaps BETWEEN merged busy intervals (and before
       the first / after the last) -- those gaps are free for everyone.
    4. Keep only gaps at least min_duration_minutes long.
    """
    from datetime import timedelta

    busy = get_busy_intervals(db, user_ids, range_start, range_end)
    merged_busy = merge_intervals(busy)

    free_slots = []
    cursor = range_start

    for busy_start, busy_end in merged_busy:
        # clip to the range we care about
        busy_start = max(busy_start, range_start)
        busy_end = min(busy_end, range_end)

        if busy_start > cursor:
            free_slots.append((cursor, busy_start))
        cursor = max(cursor, busy_end)

    if cursor < range_end:
        free_slots.append((cursor, range_end))

    min_duration = timedelta(minutes=min_duration_minutes)
    return [(s, e) for (s, e) in free_slots if (e - s) >= min_duration]

