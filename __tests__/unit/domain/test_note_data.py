"""Test suite for NoteData domain model.

This test suite verifies the functionality of the NoteData domain model,
including validation, conversion, and error handling. It ensures that the
model maintains data integrity and follows business rules.
"""

import pytest
from typing import Dict, Any

from domain.note import NoteData
from domain.values import ProcessingStatus
from domain.exceptions import (
    NoteValidationError,
    NoteContentError,
    NoteAttachmentError,
)


@pytest.fixture
def valid_note_dict() -> Dict[str, Any]:
    """Create a valid note dictionary for testing.

    This fixture provides a baseline valid note data dictionary
    that can be modified for specific test cases.
    """
    return {
        "content": "Test note content",
        "user_id": "test-user",
        "attachments": [
            {
                "type": "image",
                "url": "https://example.com/image.jpg",
            }
        ],
    }


@pytest.fixture
def valid_note_data(valid_note_dict) -> NoteData:
    """Create a valid NoteData instance for testing.

    This fixture provides a baseline valid NoteData instance
    that can be used directly in tests.
    """
    return NoteData(**valid_note_dict)


class TestNoteDataValidation:
    """Test validation methods of NoteData."""

    def test_valid_note_data(self, valid_note_data):
        """Test that valid note data passes validation."""
        # Should not raise any exceptions
        valid_note_data.validate()

    def test_invalid_content_type(self, valid_note_dict):
        """Test validation with invalid content type."""
        valid_note_dict["content"] = 123
        with pytest.raises(NoteContentError) as exc:
            NoteData(**valid_note_dict)
        assert str(exc.value) == "content must be a string"

    def test_empty_content(self, valid_note_dict):
        """Test validation with empty content."""
        valid_note_dict["content"] = ""
        with pytest.raises(NoteContentError) as exc:
            NoteData(**valid_note_dict)
        assert str(exc.value) == "content cannot be empty"

    def test_content_too_long(self, valid_note_dict):
        """Test validation with content exceeding max length."""
        valid_note_dict["content"] = "a" * 10001
        with pytest.raises(NoteContentError) as exc:
            NoteData(**valid_note_dict)
        assert (
            str(exc.value)
            == "content cannot exceed 10000 characters"
        )

    def test_invalid_user_id(self, valid_note_dict):
        """Test validation with invalid user_id."""
        valid_note_dict["user_id"] = ""
        with pytest.raises(NoteValidationError) as exc:
            NoteData(**valid_note_dict)
        assert (
            str(exc.value)
            == "user_id must be a non-empty string"
        )

    def test_invalid_attachments_type(
        self, valid_note_dict
    ):
        """Test validation with invalid attachments type."""
        valid_note_dict["attachments"] = "not a list"
        with pytest.raises(NoteAttachmentError) as exc:
            NoteData(**valid_note_dict)
        assert (
            str(exc.value) == "attachments must be a list"
        )

    def test_invalid_attachment_format(
        self, valid_note_dict
    ):
        """Test validation with invalid attachment format."""
        valid_note_dict["attachments"] = [
            {"type": "image"}
        ]  # Missing url
        with pytest.raises(NoteAttachmentError) as exc:
            NoteData(**valid_note_dict)
        assert "attachment must contain fields" in str(
            exc.value
        )

    def test_invalid_attachment_type(self, valid_note_dict):
        """Test validation with invalid attachment type."""
        valid_note_dict["attachments"] = [
            {
                "type": "invalid",
                "url": "https://example.com/file",
            }
        ]
        with pytest.raises(NoteAttachmentError) as exc:
            NoteData(**valid_note_dict)
        assert "attachment type must be one of" in str(
            exc.value
        )


class TestNoteDataConversion:
    """Test conversion methods of NoteData."""

    def test_to_dict(self, valid_note_data):
        """Test conversion to dictionary."""
        result = valid_note_data.to_dict()
        assert result["content"] == valid_note_data.content
        assert result["user_id"] == valid_note_data.user_id
        assert (
            result["attachments"]
            == valid_note_data.attachments
        )
        assert (
            result["processing_status"]
            == valid_note_data.processing_status
        )

    def test_update_content(self, valid_note_data):
        """Test updating note content."""
        new_content = "Updated content"
        valid_note_data.update_content(new_content)
        assert valid_note_data.content == new_content

    def test_update_processing_status(
        self, valid_note_data
    ):
        """Test updating processing status."""
        # Test valid transitions
        valid_note_data.update_processing_status(
            ProcessingStatus.PENDING
        )
        assert (
            valid_note_data.processing_status
            == ProcessingStatus.PENDING
        )

        valid_note_data.update_processing_status(
            ProcessingStatus.PROCESSING
        )
        assert (
            valid_note_data.processing_status
            == ProcessingStatus.PROCESSING
        )

        valid_note_data.update_processing_status(
            ProcessingStatus.COMPLETED
        )
        assert (
            valid_note_data.processing_status
            == ProcessingStatus.COMPLETED
        )

        # Test invalid transition
        with pytest.raises(ValueError) as exc:
            valid_note_data.update_processing_status(
                ProcessingStatus.PENDING
            )
        assert "Invalid transition" in str(exc.value)


class TestNoteDataErrorHandling:
    """Test error handling of NoteData."""

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        with pytest.raises(TypeError):
            NoteData()  # type: ignore

    def test_type_mismatches(self, valid_note_dict):
        """Test handling of type mismatches."""
        valid_note_dict["content"] = 123
        with pytest.raises(NoteContentError) as exc:
            NoteData(**valid_note_dict)
        assert str(exc.value) == "content must be a string"
