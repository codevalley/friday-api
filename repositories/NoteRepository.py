from typing import Optional, List
from sqlalchemy.orm import Session
from orm.NoteModel import Note
from domain.note import NoteData
from .BaseRepository import BaseRepository


class NoteRepository(BaseRepository[Note, int]):
    """Repository for managing Note entities in the database.

    This repository handles CRUD operations for notes, including
    proper conversion between domain and ORM models.
    """

    def __init__(self, db: Session):
        """Initialize the repository with a database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Note)

    def create(self, domain_data: NoteData) -> Note:
        """Create a new note from domain data.

        Args:
            domain_data: Note domain model instance

        Returns:
            Created Note ORM model instance
        """
        note = Note.from_domain(domain_data)
        return super().create(note)

    def list_notes(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Note]:
        """List notes for a specific user with pagination.

        Args:
            user_id: ID of the user whose notes to list
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Note ORM model instances
        """
        return (
            self.db.query(Note)
            .filter(Note.user_id == user_id)
            .order_by(Note.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user(
        self, note_id: int, user_id: str
    ) -> Optional[Note]:
        """Get a specific note by ID and user ID.

        Args:
            note_id: ID of the note to retrieve
            user_id: ID of the user who owns the note

        Returns:
            Note ORM model instance if found, None otherwise
        """
        return (
            self.db.query(Note)
            .filter(
                Note.id == note_id, Note.user_id == user_id
            )
            .first()
        )

    def count_user_notes(self, user_id: str) -> int:
        """Count total number of notes for a user.

        Args:
            user_id: ID of the user whose notes to count

        Returns:
            Total number of notes
        """
        return (
            self.db.query(Note)
            .filter(Note.user_id == user_id)
            .count()
        )
