"""Main application module."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from strawberry import Schema
from strawberry.fastapi import GraphQLRouter

from configs.Environment import get_environment_variables
from configs.GraphQL import get_graphql_context
from configs.Logging import configure_logging
from metadata.Tags import Tags
from routers.v1.ActivityRouter import (
    router as ActivityRouter,
)
from routers.v1.MomentRouter import router as MomentRouter
from routers.v1.AuthRouter import router as AuthRouter
from routers.v1.NoteRouter import router as NoteRouter
from schemas.graphql.Query import Query
from schemas.graphql.Mutation import Mutation
from utils.middleware.request_logging import (
    RequestLoggingMiddleware,
)
from utils.error_handlers import handle_exceptions
from utils.errors.handlers import configure_error_handlers

# Load environment variables
env = get_environment_variables()

# Determine if we're in test mode
# is_test = env.ENV_STATE == "test"

# Configure logging
configure_logging(is_test=False)

# Create FastAPI application
app = FastAPI(
    title=env.APP_NAME,
    version=env.API_VERSION,
    openapi_tags=Tags,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

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

# Include routers
app.include_router(ActivityRouter)
app.include_router(MomentRouter)
app.include_router(AuthRouter)
app.include_router(NoteRouter)

# GraphQL Configuration
schema = Schema(query=Query, mutation=Mutation)
graphql = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    graphql_ide="graphiql",
)
app.include_router(graphql, prefix="/graphql")

# Configure error handlers
configure_error_handlers(app)


# Add error handlers
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
):
    """Global exception handler for all unhandled exceptions."""
    return await handle_exceptions(request, exc)
