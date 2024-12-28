"""Service for managing notes in the system."""

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
from domain.ports.QueueService import QueueService
from domain.values import ProcessingStatus
from dependencies import get_queue

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
        queue_service: Queue service for note processing
    """

    def __init__(
        self,
        db: Session = Depends(get_db_connection),
        queue_service: QueueService = Depends(get_queue),
    ):
        """Initialize the note service.

        Args:
            db: Database session from dependency injection
            queue_service: Queue service for note processing
        """
        self.db = db
        self.note_repo = NoteRepository(db)
        self.queue_service = queue_service

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
        """Create a new note and enqueue it for processing.

        Args:
            note_data: Note creation data
            user_id: ID of the user creating the note

        Returns:
            NoteResponse: Created note data

        Raises:
            HTTPException: If note creation fails
        """
        try:
            # Convert to domain model
            domain_data = note_data.to_domain(user_id)

            # Set initial processing status
            domain_data.processing_status = (
                ProcessingStatus.PENDING
            )

            # Create note
            note = self.note_repo.create(
                content=domain_data.content,
                user_id=domain_data.user_id,
                activity_id=domain_data.activity_id,
                moment_id=domain_data.moment_id,
                attachments=domain_data.attachments,
                processing_status=domain_data.processing_status,
            )

            # Commit the transaction to ensure note has an ID
            self.db.commit()

            # Ensure note has required fields before conversion
            if note.id is None or note.created_at is None:
                raise ValueError(
                    "Note missing required fields after creation"
                )

            try:
                # Enqueue note for processing
                job_id = self.queue_service.enqueue_note(
                    note.id
                )
                if not job_id:
                    raise ValueError(
                        "Failed to enqueue note for processing"
                    )

                return NoteResponse.model_validate(
                    note.to_dict()
                )

            except Exception as e:
                logger.error(
                    "Failed to enqueue note {} for processing: {}".format(
                        note.id, str(e)
                    )
                )
                # Update status to FAILED
                note = self.note_repo.update(
                    note.id,
                    {
                        "processing_status": ProcessingStatus.FAILED
                    },
                )
                self.db.commit()
                return NoteResponse.model_validate(
                    note.to_dict()
                )

        except (
            NoteValidationError,
            NoteContentError,
            NoteAttachmentError,
            NoteReferenceError,
        ) as e:
            self._handle_note_error(e)
        except Exception as e:
            logger.error(
                f"Unexpected error creating note: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create note",
            )

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

        return NoteResponse.model_validate(note.to_dict())

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
                NoteResponse.model_validate(i.to_dict())
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
        self.db.commit()

        # Ensure updated note has required fields
        if updated.id is None or updated.created_at is None:
            raise ValueError(
                "Updated note missing required fields"
            )

        return NoteResponse.model_validate(
            updated.to_dict()
        )

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

        self.db.delete(note)
        self.db.commit()
        return True

    def get_note_processing_status(
        self, note_id: int, user_id: str
    ) -> Dict[str, Any]:
        """Get note processing status."""
        note = self.note_repo.get_by_user(note_id, user_id)
        if not note:
            raise HTTPException(
                status_code=404, detail="Note not found"
            )

        return {
            "status": note.processing_status,
            "processed_at": note.processed_at,
            "enrichment_data": note.enrichment_data,
        }

    def get_queue_health(self) -> Dict[str, Any]:
        """Get health metrics for the note processing queue.

        Returns:
            Dict containing queue health metrics
        """
        return self.queue_service.get_queue_health()
