import strawberry
from strawberry.types import Info
from fastapi import HTTPException
from typing import Optional

from schemas.pydantic.NoteSchema import (
    NoteUpdate,
)
from schemas.graphql.types.Note import Note as GQLNote
from domain.values import AttachmentType, ProcessingStatus
from configs.GraphQL import (
    get_user_from_context,
    get_db_from_context,
)
from services.NoteService import NoteService
from domain.note import NoteData


@strawberry.input
class NoteInput:
    content: str
    attachment_url: Optional[str] = None
    attachment_type: Optional[AttachmentType] = None
    processing_status: ProcessingStatus = (
        ProcessingStatus.default()
    )


@strawberry.input
class NoteUpdateInput:
    content: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_type: Optional[AttachmentType] = None
    processing_status: Optional[ProcessingStatus] = None


@strawberry.type
class NoteMutation:
    @strawberry.mutation
    def create_note(
        self, info: Info, note: NoteInput
    ) -> GQLNote:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401, detail="Unauthorized"
            )

        service = NoteService(get_db_from_context(info))
        note_data = NoteData(
            content=note.content,
            user_id=user.id,
            activity_id=note.activity_id,
            moment_id=note.moment_id,
            attachment_url=note.attachment_url,
            attachment_type=note.attachment_type,
            processing_status=note.processing_status,
        )
        result = service.create_note(note_data, user.id)
        return GQLNote.from_domain(result)

    @strawberry.mutation
    def update_note(
        self,
        info: Info,
        note_id: int,
        note: NoteUpdateInput,
    ) -> GQLNote:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401, detail="Unauthorized"
            )

        service = NoteService(get_db_from_context(info))
        update_obj = NoteUpdate(**note.__dict__)
        result = service.update_note(
            note_id, user.id, update_obj
        )
        return GQLNote.from_domain(result)

    @strawberry.mutation
    def delete_note(self, info: Info, note_id: int) -> bool:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401, detail="Unauthorized"
            )

        service = NoteService(get_db_from_context(info))
        return service.delete_note(note_id, user.id)
