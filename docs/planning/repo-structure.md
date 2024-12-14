================================================================
Repository Structure
================================================================
configs/
  Database.py
  Environment.py
  GraphQL.py
  OpenAPI.py
metadata/
  Tags.py
models/
  ActivityModel.py
  BaseModel.py
  MomentModel.py
  UserModel.py
repositories/
  ActivityRepository.py
  MomentRepository.py
  RepositoryMeta.py
  UserRepository.py
routers/
  v1/
    ActivityRouter.py
    AuthRouter.py
    MomentRouter.py
schemas/
  base/
    activity_schema.py
    moment_schema.py
    user_schema.py
  graphql/
    mutations/
      ActivityMutation.py
      MomentMutation.py
      UserMutation.py
    types/
      Activity.py
      Moment.py
      User.py
    Mutation.py
    Query.py
  pydantic/
    ActivitySchema.py
    MomentSchema.py
    PaginationSchema.py
    UserSchema.py
services/
  ActivityService.py
  MomentService.py
  UserService.py
utils/
  json_utils.py
  security.py
dependencies.py
main.py