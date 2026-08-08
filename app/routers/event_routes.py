"""
Event routes: create events, list events, get one event.

The interesting part is in create_event: BEFORE saving a new event,
we check the host AND every invited participant for conflicts using
scheduling.get_conflicting_events(). This is "double-booking
prevention" -- the core feature of the whole project.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas, auth, scheduling

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=schemas.EventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: schemas.EventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if event_in.end_time <= event_in.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    # Everyone who needs to be free for this event: the host + invited participants
    all_involved_ids = set(event_in.participant_ids) | {current_user.id}

    conflicts_by_user = {}
    for user_id in all_involved_ids:
        conflicts = scheduling.get_conflicting_events(
            db, user_id, event_in.start_time, event_in.end_time
        )
        if conflicts:
            conflicts_by_user[user_id] = [c.id for c in conflicts]

    if conflicts_by_user:
        # 409 Conflict is the correct HTTP status for "this collides with existing data"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "One or more participants have a conflicting event",
                "conflicts": conflicts_by_user,  # {user_id: [conflicting_event_ids]}
            },
        )

    event = models.Event(
        host_id=current_user.id,
        title=event_in.title,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
    )
    db.add(event)
    db.flush()  # assigns event.id without fully committing yet

    for user_id in event_in.participant_ids:
        db.add(models.Participant(event_id=event.id, user_id=user_id))

    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=List[schemas.EventOut])
def list_my_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Events where the current user is either the host or a participant."""
    hosted = db.query(models.Event).filter(models.Event.host_id == current_user.id)
    participating = (
        db.query(models.Event)
        .join(models.Participant)
        .filter(models.Participant.user_id == current_user.id)
    )
    return hosted.union(participating).all()


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    involved_ids = {event.host_id} | {p.user_id for p in event.participants}
    if current_user.id not in involved_ids:
        raise HTTPException(status_code=403, detail="Not part of this event")

    return event


@router.post("/find-common-free-slots", response_model=List[schemas.FreeSlotOut])
def find_common_free_slots(
    request: schemas.FreeSlotRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    'When can all these people meet?'

    Give it a list of user_ids and a time range, and it returns every
    gap of at least min_duration_minutes where NONE of them are busy.
    This is the standout feature: it isn't just checking one pair of
    times, it's reasoning about everyone's schedules together.
    """
    if request.range_end <= request.range_start:
        raise HTTPException(status_code=400, detail="range_end must be after range_start")

    slots = scheduling.find_common_free_slots(
        db,
        user_ids=request.user_ids,
        range_start=request.range_start,
        range_end=request.range_end,
        min_duration_minutes=request.min_duration_minutes,
    )
    return [{"start_time": s, "end_time": e} for s, e in slots]
