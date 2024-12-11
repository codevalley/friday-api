from fastapi import Depends, FastAPI
from strawberry import Schema
from strawberry.fastapi import GraphQLRouter

from configs.Environment import get_environment_variables
from configs.GraphQL import get_graphql_context
from metadata.Tags import Tags
from models.BaseModel import init
from routers.v1.ActivityRouter import router as ActivityRouter
from routers.v1.MomentRouter import router as MomentRouter
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

# Add Routers
app.include_router(ActivityRouter)
app.include_router(MomentRouter)

# GraphQL Schema and Application Instance
schema = Schema(query=Query, mutation=Mutation)
graphql = GraphQLRouter(
    schema,
    graphiql=env.DEBUG_MODE,
    context_getter=get_graphql_context,
)

# Integrate GraphQL Application to the Core one
app.include_router(
    graphql,
    prefix="/graphql",
    include_in_schema=False,
)

# Initialise Data Model Attributes
init()
