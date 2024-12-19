from fastapi import FastAPI
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
from schemas.graphql.Query import Query
from schemas.graphql.Mutation import Mutation
from utils.middleware.request_logging import (
    RequestLoggingMiddleware,
)

# Configure logging
configure_logging(is_test=False)

# Application Environment Configuration
env = get_environment_variables()

# FastAPI Configuration
app = FastAPI(
    title=env.APP_NAME,
    version=env.API_VERSION,
    openapi_tags=Tags,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Configuration
app.add_middleware(RequestLoggingMiddleware)

# REST API Configuration
app.include_router(ActivityRouter)
app.include_router(MomentRouter)
app.include_router(AuthRouter)

# GraphQL Configuration
schema = Schema(query=Query, mutation=Mutation)
graphql = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    graphql_ide="graphiql",
)
app.include_router(graphql, prefix="/graphql")
