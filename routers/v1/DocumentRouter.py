"""Router for document-related operations."""

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
    DocumentUpdate,
    DocumentResponse,
    DocumentStatusUpdate,
)
from schemas.pydantic.CommonSchema import (
    GenericResponse,
    PaginatedResponse,
)
from schemas.pydantic.StorageSchema import (
    StorageUsageResponse,
)
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

# Create routers
router = APIRouter(
    prefix="/v1/docs",
    tags=["documents"],
)

# Protected routes require authentication
protected_router = APIRouter(
    dependencies=[Depends(auth_scheme)],
)

# Public routes do not require authentication
public_router = APIRouter()


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
    status_code=status.HTTP_201_CREATED,
)
@handle_exceptions
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    mime_type: str = Form(...),
    metadata: str = Form(None),
    is_public: bool = Form(False),
    unique_name: str = Form(None),
    user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(
        get_document_service
    ),
) -> GenericResponse[DocumentResponse]:
    """Upload a document."""
    # Read file content synchronously
    file_content = file.file.read()

    # Parse metadata
    metadata_dict = json.loads(metadata) if metadata else {}

    # Create document
    result = document_service.create_document(
        name=name,
        mime_type=mime_type,
        file_content=file_content,
        file_size=len(file_content),
        metadata=metadata_dict,
        is_public=is_public,
        unique_name=unique_name,
        user_id=user.id,
    )
    return GenericResponse(data=result)


@protected_router.get(
    "/",
    response_model=GenericResponse[
        PaginatedResponse[DocumentResponse]
    ],
)
@handle_exceptions
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[PaginatedResponse[DocumentResponse]]:
    """List documents."""
    result = service.list_documents(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    total = service.count_documents(user_id=current_user.id)
    pages = (total + limit - 1) // limit
    paginated_response = PaginatedResponse(
        items=result,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
    )
    return GenericResponse(
        data=paginated_response,
        message=f"Retrieved {total} documents",
    )


@protected_router.get(
    "/storage/usage",
    response_model=GenericResponse[StorageUsageResponse],
)
@handle_exceptions
async def get_storage_usage(
    user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(
        get_document_service
    ),
) -> GenericResponse[StorageUsageResponse]:
    """Get storage usage."""
    result = document_service.get_storage_usage(user.id)
    return GenericResponse(
        data=result,
        message="Storage usage retrieved successfully",
    )


@protected_router.get(
    "/{document_id}",
    response_model=GenericResponse[DocumentResponse],
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
    result = service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )
    return GenericResponse(
        data=result,
        message="Document retrieved successfully",
    )


@protected_router.put(
    "/{document_id}",
    response_model=GenericResponse[DocumentResponse],
)
@handle_exceptions
async def update_document(
    document_id: int,
    document: DocumentUpdate = Body(...),
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Update a document."""
    result = service.update_document(
        document_id=document_id,
        user_id=current_user.id,
        update_data=document,
    )
    return GenericResponse(
        data=result, message="Document updated successfully"
    )


@protected_router.put(
    "/{document_id}/status",
    response_model=GenericResponse[DocumentResponse],
)
@handle_exceptions
async def update_document_status(
    document_id: int,
    status_update: DocumentStatusUpdate,
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[DocumentResponse]:
    """Update a document's status."""
    result = service.update_document_status(
        document_id=document_id,
        user_id=current_user.id,
        new_status=status_update.status,
    )
    return GenericResponse(
        data=result,
        message="Document status updated successfully",
    )


@protected_router.get(
    "/{document_id}/content",
    response_class=StreamingResponse,
)
@handle_exceptions
async def get_document_content(
    document_id: int,
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Get document content.

    Returns the actual file content of the document.
    """
    # First get document metadata to get mime_type
    doc = service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )

    # Then get the content
    content = service.get_document_content(
        document_id=document_id,
        user_id=current_user.id,
        owner_id=doc.user_id,  # Pass the document owner's ID
    )

    return StreamingResponse(
        iter([content.getvalue()]),
        media_type=doc.mime_type,
    )


@protected_router.delete(
    "/{document_id}",
    response_model=GenericResponse[None],
)
@handle_exceptions
async def delete_document(
    document_id: int,
    service: DocumentService = Depends(
        get_document_service
    ),
    current_user: User = Depends(get_current_user),
) -> GenericResponse[None]:
    """Delete a document."""
    service.delete_document(
        document_id=document_id,
        user_id=current_user.id,
    )
    return GenericResponse(
        data=None, message="Document deleted successfully"
    )


@public_router.get(
    "/public/{unique_name}",
    response_model=GenericResponse[DocumentResponse],
)
@handle_exceptions
async def get_public_document(
    unique_name: str,
    service: DocumentService = Depends(
        get_document_service
    ),
) -> GenericResponse[DocumentResponse]:
    """Get a public document by its unique name."""
    try:
        result = service.get_public_document(
            unique_name=unique_name
        )
        return GenericResponse(
            data=result,
            message="Document retrieved successfully",
        )
    except Exception as e:
        print(f"Error in get_public_document: {str(e)}")
        raise


@public_router.get(
    "/public/{unique_name}/download",
    response_class=StreamingResponse,
)
@handle_exceptions
async def download_public_document(
    unique_name: str,
    service: DocumentService = Depends(
        get_document_service
    ),
) -> StreamingResponse:
    """Download a public document."""
    # First get document metadata
    doc = service.get_public_document(unique_name)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Then get the content
    content = service.get_document_content(
        document_id=doc.id,
        user_id=doc.user_id,  # Use document owner's ID as the requesting user
        owner_id=doc.user_id,  # Pass the document owner's ID
    )

    return StreamingResponse(
        iter([content.getvalue()]),
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{doc.name}"'
        },
    )


# Add routes to protected router
protected_router.post(
    "/upload",
    response_model=GenericResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)(upload_document)

protected_router.get(
    "/",
    response_model=GenericResponse[
        PaginatedResponse[DocumentResponse]
    ],
)(list_documents)

protected_router.get(
    "/storage/usage",
    response_model=GenericResponse[StorageUsageResponse],
)(get_storage_usage)

protected_router.get(
    "/{document_id}",
    response_model=GenericResponse[DocumentResponse],
)(get_document)

protected_router.get(
    "/{document_id}/content",
    response_class=StreamingResponse,
)(get_document_content)

protected_router.put(
    "/{document_id}",
    response_model=GenericResponse[DocumentResponse],
)(update_document)

protected_router.put(
    "/{document_id}/status",
    response_model=GenericResponse[DocumentResponse],
)(update_document_status)

protected_router.delete(
    "/{document_id}",
    response_model=GenericResponse[None],
)(delete_document)

# Add routes to public router
public_router.get(
    "/public/{unique_name}",
    response_model=GenericResponse[DocumentResponse],
)(get_public_document)

public_router.get(
    "/public/{unique_name}/download",
    response_class=StreamingResponse,
)(download_public_document)

# Include protected routes
router.include_router(protected_router)
router.include_router(public_router)
