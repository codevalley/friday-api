from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry import Schema
from strawberry.fastapi import GraphQLRouter

from configs.Environment import get_environment_variables
from configs.GraphQL import get_graphql_context
from metadata.Tags import Tags
from models.BaseModel import init
from routers.v1.ActivityRouter import (
    router as ActivityRouter,
)
from routers.v1.MomentRouter import router as MomentRouter
from routers.v1.AuthRouter import router as AuthRouter
from schemas.graphql.Query import Query
from schemas.graphql.Mutation import Mutation

# Application Environment Configuration
env = get_environment_variables()

# Core Application Instance
app = FastAPI(
    title="Friday API",
    description="A powerful life logging API built with FastAPI and GraphQL. Track your daily activities and moments with rich, structured data.",
    version=env.API_VERSION,
    openapi_tags=Tags,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure security scheme for OpenAPI
app.openapi_components = {
    "securitySchemes": {
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter your bearer token in the format: Bearer <token>",
        }
    }
}
app.openapi_security = [{"Bearer": []}]

# Add Routers
app.include_router(ActivityRouter)
app.include_router(MomentRouter)
app.include_router(AuthRouter)

# GraphQL Configuration
schema = Schema(query=Query, mutation=Mutation)
graphql = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    graphiql=True,
)
app.include_router(graphql, prefix="/graphql")

# Initialize Database
init()
