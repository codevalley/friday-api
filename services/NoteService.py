from typing import Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from repositories.NoteRepository import NoteRepository
from schemas.pydantic.NoteSchema import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
)
from utils.validation import validate_pagination

import logging

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

    def create_note(
        self, note_data: NoteCreate, user_id: str
    ) -> NoteResponse:
        """Create a new note for a user.

        Args:
            note_data: Note creation data
            user_id: ID of the user creating the note

        Returns:
            Created note response
        """
        domain_data = note_data.to_domain(user_id)
        instance = self.note_repo.create(domain_data)
        return NoteResponse.from_orm(instance)

    def get_note(
        self, note_id: int, user_id: str
    ) -> NoteResponse:
        """Get a specific note by ID.

        Args:
            note_id: ID of the note to retrieve
            user_id: ID of the user requesting the note

        Returns:
            Note response if found

        Raises:
            HTTPException: If note is not found
        """
        note = self.note_repo.get_by_user(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=404, detail="Note not found"
            )
        return NoteResponse.from_orm(note)

    def list_notes(
        self, user_id: str, page: int = 1, size: int = 50
    ) -> Dict[str, Any]:
        """List notes for a user with pagination.

        Args:
            user_id: ID of the user whose notes to list
            page: Page number (1-based)
            size: Number of items per page

        Returns:
            Dictionary containing:
                - items: List of notes
                - total: Total number of notes
                - page: Current page number
                - size: Page size
                - pages: Total number of pages
        """
        validate_pagination(page, size)
        skip = (page - 1) * size
        items = self.note_repo.list_notes(
            user_id, skip=skip, limit=size
        )
        total = self.note_repo.count_user_notes(user_id)
        return {
            "items": [
                NoteResponse.from_orm(i) for i in items
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
        """Update a specific note.

        Args:
            note_id: ID of the note to update
            user_id: ID of the user updating the note
            update_data: New note data

        Returns:
            Updated note response

        Raises:
            HTTPException: If note is not found
        """
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
        return NoteResponse.from_orm(updated)

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
