"""Router for document-related operations."""

from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    Query,
    status,
    Body,
    Form,
)
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
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
    GenericResponse,
)
from schemas.pydantic.StorageSchema import (
    StorageUsageResponse,
)
from domain.document import DocumentStatus
from dependencies import get_current_user
from orm.UserModel import User
from utils.error_handlers import handle_exceptions
from auth.bearer import CustomHTTPBearer
from configs.Database import get_db_connection
from repositories.DocumentRepository import (
    DocumentRepository,
)
from infrastructure.storage.factory import StorageFactory
import json

# Use our custom bearer that returns 401 for invalid tokens
auth_scheme = CustomHTTPBearer()

router = APIRouter(
    prefix="/docs",
    tags=["documents"],
)

# Protected endpoints
protected_router = APIRouter()


def get_document_service(
    db=Depends(get_db_connection),
) -> DocumentService:
    """Get document service instance."""
    repository = DocumentRepository(db)
    storage_service = (
        StorageFactory.create_storage_service()
    )
    return DocumentService(
        repository=repository,
        storage=storage_service,
    )


@protected_router.post(
    "/upload",
    response_model=GenericResponse[DocumentResponse],
    dependencies=[Depends(auth_scheme)],
    status_code=status.HTTP_201_CREATED,
)
@handle_exceptions
async def upload_document(
    name: str = Form(...),
    mime_type: str = Form(...),
    metadata: Optional[str] = Form(None),
    is_public: str = Form(
        "false"
    ),  # Form values come as strings
    unique_name: Optional[str] = Form(
        ""
    ),  # Empty string for None
    file: UploadFile = File(...),
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Upload a new document.

    This endpoint handles both file upload and document metadata creation.
    The file will be stored and a document record will be created with
    its metadata.
    """
    # Convert metadata string to dict if provided
    metadata_dict = (
        json.loads(metadata)
        if metadata and metadata.strip()
        else None
    )

    # Convert form values to appropriate types
    is_public_bool = is_public.lower() == "true"
    unique_name_clean = (
        unique_name
        if unique_name and unique_name.strip()
        else None
    )

    # Create document data
    document = DocumentCreate(
        name=name,
        mime_type=mime_type,
        metadata=metadata_dict,
        is_public=is_public_bool,
        unique_name=unique_name_clean,
    )

    result = await service.create_document(
        document=document,
        user_id=current_user.id,
        file=file,
    )
    return GenericResponse(
        data=result,
        message="Document uploaded successfully",
    )


@protected_router.get(
    "",
    response_model=GenericResponse[List[DocumentResponse]],
    dependencies=[Depends(auth_scheme)],
)
@handle_exceptions
async def list_documents(
    pagination: PaginationParams = Depends(),
    status: Optional[DocumentStatus] = None,
    mime_type: Optional[str] = Query(None),
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[List[DocumentResponse]]:
    """List documents with filtering and pagination.

    Args:
        pagination: Pagination parameters
        status: Filter by document status
        mime_type: Filter by MIME type
    """
    # Convert page and size to skip and limit
    skip = (pagination.page - 1) * pagination.size
    limit = pagination.size

    documents = await service.get_user_documents(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status,
        mime_type=mime_type,
    )

    return GenericResponse(
        data=documents,
        message="Documents retrieved successfully",
    )


@protected_router.get(
    "/storage-usage",
    response_model=GenericResponse[StorageUsageResponse],
    dependencies=[Depends(auth_scheme)],
)
@handle_exceptions
async def get_storage_usage(
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[StorageUsageResponse]:
    """Get total storage usage for the current user."""
    total_bytes = await service.get_user_storage_usage(
        user_id=current_user.id,
    )
    return GenericResponse(
        data=StorageUsageResponse(usage_bytes=total_bytes),
        message="Storage usage retrieved successfully",
    )


@protected_router.get(
    "/{document_id}",
    response_model=GenericResponse[DocumentResponse],
    dependencies=[Depends(auth_scheme)],
)
@handle_exceptions
async def get_document(
    document_id: int,
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Get a specific document by ID."""
    document = await service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )
    return GenericResponse(
        data=document,
        message="Document retrieved successfully",
    )


@protected_router.patch(
    "/{document_id}",
    response_model=GenericResponse[DocumentResponse],
    dependencies=[Depends(auth_scheme)],
)
@handle_exceptions
async def update_document(
    document_id: int,
    document: DocumentUpdate,
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Update a document's metadata."""
    updated_doc = await service.update_document(
        document_id=document_id,
        user_id=current_user.id,
        update_data=document,
    )
    return GenericResponse(
        data=updated_doc,
        message="Document updated successfully",
    )


@protected_router.patch(
    "/{document_id}/status",
    response_model=GenericResponse[DocumentResponse],
    dependencies=[Depends(auth_scheme)],
)
@handle_exceptions
async def update_document_status(
    document_id: int,
    status_update: dict = Body(...),
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Update a document's status."""
    try:
        new_status = DocumentStatus(status_update["status"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status value ",
        )

    updated_doc = await service.update_document_status(
        document_id=document_id,
        user_id=current_user.id,
        new_status=new_status,
    )
    return GenericResponse(
        data=updated_doc,
        message="Document status updated successfully",
    )


@protected_router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth_scheme)],
)
@handle_exceptions
async def delete_document(
    document_id: int,
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a document."""
    await service.delete_document(
        document_id=document_id,
        user_id=current_user.id,
    )


# Public endpoints
@router.get(
    "/public/{document_id}",
    response_model=GenericResponse[DocumentResponse],
)
@handle_exceptions
async def get_public_document(
    document_id: int,
    service: DocumentService = Depends(
        get_document_service
    ),
) -> GenericResponse[DocumentResponse]:
    """Get a public document by ID."""
    document = await service.get_public_document(
        document_id=document_id,
    )
    return GenericResponse[DocumentResponse](
        data=document,
        message="Public document retrieved successfully",
    )


@router.get(
    "/public/{document_id}/download",
)
@handle_exceptions
async def download_public_document(
    document_id: int,
    service: DocumentService = Depends(
        get_document_service
    ),
) -> StreamingResponse:
    """Download a public document."""
    (
        document,
        content,
    ) = await service.get_public_document_content(
        document_id=document_id,
    )
    return StreamingResponse(
        content,
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={document.name}",
        },
    )


# Include protected routes
router.include_router(protected_router, prefix="/protected")
