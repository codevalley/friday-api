"""Router for Document-related endpoints."""

from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    Query,
    status,
)
from services.DocumentService import DocumentService
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)
from schemas.pydantic.PaginationSchema import (
    PaginationParams,
)
from schemas.pydantic.CommonSchema import (
    MessageResponse,
    GenericResponse,
)
from domain.document import DocumentStatus
from dependencies import get_current_user
from orm.UserModel import User
from utils.error_handlers import handle_exceptions
from auth.bearer import CustomHTTPBearer

# Use our custom bearer that returns 401 for invalid tokens
auth_scheme = CustomHTTPBearer()

router = APIRouter(
    prefix="/v1/documents",
    tags=["documents"],
    dependencies=[Depends(auth_scheme)],
)


@router.post(
    "/upload",
    response_model=GenericResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
@handle_exceptions
async def upload_document(
    document: DocumentCreate,
    file: UploadFile = File(...),
    service: DocumentService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Upload a new document.

    This endpoint handles both file upload and document metadata creation.
    The file will be stored and a document record will be created with
    its metadata.
    """
    # TODO: Implement file storage service integration
    storage_url = f"local://documents/{file.filename}"

    result = service.create_document(
        document=document,
        user_id=current_user.id,
        file=file,
        storage_url=storage_url,
    )
    return GenericResponse(
        data=result,
        message="Document uploaded successfully",
    )


@router.get(
    "",
    response_model=GenericResponse[List[DocumentResponse]],
)
@handle_exceptions
async def list_documents(
    pagination: PaginationParams = Depends(),
    status: Optional[DocumentStatus] = None,
    mime_type: Optional[str] = Query(None),
    service: DocumentService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[List[DocumentResponse]]:
    """List documents with filtering and pagination.

    Args:
        pagination: Pagination parameters
        status: Filter by document status
        mime_type: Filter by MIME type
    """
    documents = service.get_user_documents(
        user_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        status=status,
        mime_type=mime_type,
    )
    return GenericResponse(
        data=documents,
        message="Documents retrieved successfully",
    )


@router.get(
    "/{document_id}",
    response_model=GenericResponse[DocumentResponse],
)
@handle_exceptions
async def get_document(
    document_id: int,
    service: DocumentService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Get a specific document by ID."""
    document = service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )
    return GenericResponse(
        data=document,
        message="Document retrieved successfully",
    )


@router.patch(
    "/{document_id}",
    response_model=GenericResponse[DocumentResponse],
)
@handle_exceptions
async def update_document(
    document_id: int,
    document: DocumentUpdate,
    service: DocumentService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Update a document's metadata."""
    result = service.update_document(
        document_id=document_id,
        user_id=current_user.id,
        update_data=document,
    )
    return GenericResponse(
        data=result,
        message="Document updated successfully",
    )


@router.patch(
    "/{document_id}/status",
    response_model=GenericResponse[DocumentResponse],
)
@handle_exceptions
async def update_document_status(
    document_id: int,
    status: DocumentStatus,
    service: DocumentService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Update a document's status."""
    result = service.update_document_status(
        document_id=document_id,
        user_id=current_user.id,
        new_status=status,
    )
    return GenericResponse(
        data=result,
        message="Document status updated successfully",
    )


@router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
@handle_exceptions
async def delete_document(
    document_id: int,
    service: DocumentService = Depends(),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Delete a document."""
    service.delete_document(
        document_id=document_id,
        user_id=current_user.id,
    )
    return MessageResponse(
        message="Document deleted successfully"
    )


@router.get(
    "/storage/usage",
    response_model=GenericResponse[int],
)
@handle_exceptions
async def get_storage_usage(
    service: DocumentService = Depends(),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[int]:
    """Get total storage usage for the current user."""
    usage = service.get_user_storage_usage(current_user.id)
    return GenericResponse(
        data=usage,
        message="Storage usage retrieved successfully",
    )
