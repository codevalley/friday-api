"""Repository for managing notes in the database."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from domain.values import ProcessingStatus
from orm.NoteModel import Note


class NoteRepository:
    """Repository for managing notes in the database."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def create(
        self,
        content: str,
        user_id: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        processing_status: ProcessingStatus = ProcessingStatus.PENDING,
    ) -> Note:
        """Create a new note.

        Args:
            content: Note content
            user_id: ID of the user creating the note
            attachments: Optional list of attachments
            processing_status: Initial processing status

        Returns:
            Note: Created note
        """
        note = Note(
            content=content,
            user_id=user_id,
            attachments=attachments or [],
            processing_status=processing_status,
        )
        self.session.add(note)
        self.session.flush()  # Ensure note gets an ID
        return note

    def get_by_id(self, note_id: int) -> Optional[Note]:
        """Get note by ID.

        Args:
            note_id: ID of the note to retrieve

        Returns:
            Note if found, None otherwise
        """
        return self.session.get(Note, note_id)

    def get(self, note_id: int) -> Optional[Note]:
        """Get note by ID (alias for get_by_id).

        Args:
            note_id: ID of the note to retrieve

        Returns:
            Note if found, None otherwise
        """
        return self.get_by_id(note_id)

    def get_by_user(
        self, note_id: int, user_id: str
    ) -> Optional[Note]:
        """Get note by ID and user ID.

        Args:
            note_id: ID of the note to retrieve
            user_id: ID of the user who owns the note

        Returns:
            Note if found and owned by user, None otherwise
        """
        return (
            self.session.query(Note)
            .filter(
                Note.id == note_id,
                Note.user_id == user_id,
            )
            .first()
        )

    def list_notes(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Note]:
        """List notes for a user with pagination.

        Args:
            user_id: ID of the user whose notes to list
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Note]: List of notes
        """
        return (
            self.session.query(Note)
            .filter(Note.user_id == user_id)
            .order_by(Note.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_user_notes(self, user_id: str) -> int:
        """Count total notes for a user.

        Args:
            user_id: ID of the user whose notes to count

        Returns:
            int: Total number of notes
        """
        return (
            self.session.query(Note)
            .filter(Note.user_id == user_id)
            .count()
        )

    def update(
        self, note_id: int, data: Dict[str, Any]
    ) -> Note:
        """Update a note.

        Args:
            note_id: ID of the note to update
            data: Dictionary of fields to update

        Returns:
            Note: Updated note

        Raises:
            ValueError: If note is not found
        """
        note = self.get_by_id(note_id)
        if not note:
            raise ValueError(f"Note {note_id} not found")

        for key, value in data.items():
            if key == "processing_status":
                if isinstance(value, ProcessingStatus):
                    # Keep as enum if it's already an enum
                    setattr(note, key, value)
                else:
                    # Convert string to enum if it's a string
                    setattr(
                        note, key, ProcessingStatus(value)
                    )
            else:
                setattr(note, key, value)

        self.session.add(note)
        self.session.flush()  # Send changes to DB
        return note
