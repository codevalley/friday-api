from fastapi import APIRouter, Depends, status
from services.NoteService import NoteService
from schemas.pydantic.NoteSchema import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
)
from schemas.pydantic.CommonSchema import (
    GenericResponse,
    MessageResponse,
)
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
from dependencies import get_current_user
from orm.UserModel import User
from utils.error_handlers import handle_exceptions
from sqlalchemy.orm import Session
from configs.Database import get_db_connection

router = APIRouter(
    prefix="/v1/notes",
    tags=["notes"]
)


@router.post(
    "",
    response_model=GenericResponse[NoteResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    note: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_connection),
) -> GenericResponse[NoteResponse]:
    """Create a new note."""
    service = NoteService(db)
    result = service.create_note(note, current_user.id)
    return GenericResponse(
        data=result, message="Note created successfully"
    )


@router.get("", response_model=GenericResponse[dict])
@handle_exceptions
async def list_notes(
    pagination: PaginationParams = Depends(),
    service: NoteService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """List all notes for the current user with pagination."""
    result = service.list_notes(
        current_user.id, pagination.page, pagination.size
    )
    return GenericResponse(
        data=result,
        message=f"Retrieved {result['total']} notes",
    )


@router.get(
    "/{note_id}",
    response_model=GenericResponse[NoteResponse],
)
@handle_exceptions
async def get_note(
    note_id: int,
    service: NoteService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Get a specific note by ID."""
    result = service.get_note(note_id, current_user.id)
    return GenericResponse(data=result)


@router.put(
    "/{note_id}",
    response_model=GenericResponse[NoteResponse],
)
@handle_exceptions
async def update_note(
    note_id: int,
    note: NoteUpdate,
    service: NoteService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Update a specific note by ID."""
    result = service.update_note(
        note_id, current_user.id, note
    )
    return GenericResponse(
        data=result, message="Note updated successfully"
    )


@router.delete(
    "/{note_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
@handle_exceptions
async def delete_note(
    note_id: int,
    service: NoteService = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific note by ID."""
    service.delete_note(note_id, current_user.id)
    return MessageResponse(
        message="Note deleted successfully"
    )
