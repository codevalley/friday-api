from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from repositories.NoteRepository import NoteRepository
from schemas.pydantic.NoteSchema import (
    NoteUpdate,
    NoteResponse,
    NoteCreate,
)
from utils.validation import validate_pagination

import logging

from domain.exceptions import (
    NoteValidationError,
    NoteContentError,
    NoteAttachmentError,
    NoteReferenceError,
)

logger = logging.getLogger(__name__)


class NoteService:
    """Service for managing notes in the system.

    This service handles the business logic for creating, reading, updating,
    and deleting notes. It ensures proper validation and authorization.

    Attributes:
        db: Database session
        note_repo: Repository for note operations
    """

    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        """Initialize the note service.

        Args:
            db: Database session from dependency injection
        """
        self.db = db
        self.note_repo = NoteRepository(db)

    def _handle_note_error(self, error: Exception) -> None:
        """Map domain exceptions to HTTP exceptions."""
        if isinstance(error, NoteContentError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        elif isinstance(error, NoteAttachmentError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        elif isinstance(error, NoteReferenceError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        elif isinstance(error, NoteValidationError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(error),
                    "code": error.code,
                },
            )
        raise error

    def create_note(
        self,
        note_data: NoteCreate,
        user_id: str,
    ) -> NoteResponse:
        """Create a new note."""
        try:
            # Convert to domain model
            domain_data = note_data.to_domain(user_id)

            # Create note
            note = self.note_repo.create(
                content=domain_data.content,
                user_id=domain_data.user_id,
                activity_id=domain_data.activity_id,
                moment_id=domain_data.moment_id,
                attachments=domain_data.attachments,
            )

            # Ensure note has required fields before conversion
            if note.id is None or note.created_at is None:
                raise ValueError(
                    "Note missing required fields after creation"
                )

            return NoteResponse.model_validate(note)
        except (
            NoteValidationError,
            NoteContentError,
            NoteAttachmentError,
            NoteReferenceError,
        ) as e:
            self._handle_note_error(e)

    def get_note(
        self, note_id: int, user_id: str
    ) -> NoteResponse:
        """Get a specific note by ID."""
        note = self.note_repo.get_by_user(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=404, detail="Note not found"
            )

        # Ensure note has required fields before conversion
        if note.id is None or note.created_at is None:
            raise ValueError("Note missing required fields")

        return NoteResponse.model_validate(note)

    def list_notes(
        self, user_id: str, page: int = 1, size: int = 50
    ) -> Dict[str, Any]:
        """List notes for a user with pagination."""
        validate_pagination(page, size)
        skip = (page - 1) * size
        items = self.note_repo.list_notes(
            user_id, skip=skip, limit=size
        )
        total = self.note_repo.count_user_notes(user_id)
        return {
            "items": [
                NoteResponse.model_validate(i)
                for i in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    def update_note(
        self,
        note_id: int,
        user_id: str,
        update_data: NoteUpdate,
    ) -> NoteResponse:
        """Update a specific note."""
        note = self.note_repo.get_by_user(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=404, detail="Note not found"
            )

        data_to_update = update_data.dict(
            exclude_unset=True
        )
        updated = self.note_repo.update(
            note_id, data_to_update
        )

        # Ensure updated note has required fields
        if updated.id is None or updated.created_at is None:
            raise ValueError(
                "Updated note missing required fields"
            )

        return NoteResponse.model_validate(updated)

    def delete_note(
        self, note_id: int, user_id: str
    ) -> bool:
        """Delete a specific note.

        Args:
            note_id: ID of the note to delete
            user_id: ID of the user deleting the note

        Returns:
            True if deletion was successful

        Raises:
            HTTPException: If note is not found
        """
        note = self.note_repo.get_by_user(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=404, detail="Note not found"
            )

        self.note_repo.delete(note_id)
        return True
