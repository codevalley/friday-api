"""Main application module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from configs.Environment import get_environment_variables
from configs.Logging import configure_logging
from configs.OpenAPI import configure_openapi
from configs.queue_dependencies import get_queue_service
from routers.v1.ActivityRouter import (
    router as activity_router,
)
from routers.v1.AuthRouter import router as auth_router
from routers.v1.MomentRouter import router as moment_router
from routers.v1.NoteRouter import router as note_router
from routers.v1.TaskRouter import router as task_router
from utils.middleware.request_logging import (
    RequestLoggingMiddleware,
)

# Get environment variables
env = get_environment_variables()

# Configure logging
configure_logging()

# Create FastAPI app
app = FastAPI()

# Configure OpenAPI
configure_openapi(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add routers
app.include_router(auth_router)
app.include_router(activity_router)
app.include_router(moment_router)
app.include_router(note_router)
app.include_router(task_router)


# Add dependencies
def get_queue_service_override():
    """Override QueueService dependency."""
    return get_queue_service()


app.dependency_overrides[
    get_queue_service
] = get_queue_service_override
