from typing import List, Optional
from datetime import datetime

import strawberry
from strawberry.types import Info
from fastapi import HTTPException
from configs.GraphQL import (
    get_ActivityService,
    get_MomentService,
    get_user_from_context,
    get_db_from_context,
)

from schemas.graphql.types.Activity import (
    Activity,
    ActivityConnection,
)
from schemas.graphql.types.Moment import (
    Moment,
    MomentConnection,
)
from schemas.graphql.types.Note import Note as GQLNote
from schemas.graphql.types.Task import Task, TaskConnection
from services.NoteService import NoteService
from services.TaskService import TaskService
from domain.values import TaskStatus, TaskPriority


@strawberry.type(description="Query all entities")
class Query:
    @strawberry.field(description="Get an Activity by ID")
    def getActivity(
        self, id: int, info: Info
    ) -> Optional[Activity]:
        """Get an activity by ID

        Args:
            id: Activity ID
            info: GraphQL request info

        Returns:
            Activity if found, None otherwise

        Raises:
            HTTPException: If user is not authenticated
        """
        activity_service = get_ActivityService(info)
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to get activity",
            )
        return activity_service.get_activity_graphql(
            id, str(user.id)
        )

    @strawberry.field(description="List all Activities")
    def getActivities(
        self,
        info: Info,
        page: int = 1,
        size: int = 50,
    ) -> ActivityConnection:
        """List all activities with pagination

        Args:
            info: GraphQL request info
            page: Page number (1-based)
            size: Items per page

        Returns:
            Paginated list of activities

        Raises:
            HTTPException: If user is not authenticated
        """
        activity_service = get_ActivityService(info)
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to list activities",
            )

        activities = activity_service.list_activities(
            user_id=str(user.id),
            page=page,
            size=size,
        )

        return ActivityConnection(
            items=activities,
            total=len(activities),
            page=page,
            size=size,
        )

    @strawberry.field(description="Get a moment by ID")
    def getMoment(
        self, id: int, info: Info
    ) -> Optional[Moment]:
        """Get a moment by ID

        Args:
            id: Moment ID
            info: GraphQL request info

        Returns:
            Moment if found, None otherwise

        Raises:
            HTTPException: If user is not authenticated
        """
        moment_service = get_MomentService(info)
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to get moment",
            )
        return moment_service.get_moment_graphql(
            id, str(user.id)
        )

    @strawberry.field(
        description="Get moments with pagination"
    )
    def getMoments(
        self,
        info: Info,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> MomentConnection:
        """Get moments with pagination and filtering

        Args:
            info: GraphQL request info
            page: Page number (1-based)
            size: Items per page
            activity_id: Optional activity ID filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Paginated list of moments

        Raises:
            HTTPException: If user is not authenticated
        """
        moment_service = get_MomentService(info)
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to list moments",
            )

        moments = moment_service.list_moments(
            page=page,
            size=size,
            activity_id=activity_id,
            start_date=start_time,
            end_date=end_time,
            user_id=str(user.id),
        )
        return MomentConnection.from_pydantic(moments)

    @strawberry.field(
        description="Get recently used activities"
    )
    def getRecentActivities(
        self, info: Info, limit: int = 5
    ) -> List[Activity]:
        """Get recently used activities

        Args:
            info: GraphQL request info
            limit: Maximum number of activities to return

        Returns:
            List of recently used activities

        Raises:
            HTTPException: If user is not authenticated
        """
        moment_service = get_MomentService(info)
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to get recent activities",
            )

        return moment_service.list_recent_activities(
            str(user.id), limit
        )

    @strawberry.field(description="Get a Note by ID")
    def get_note(
        self, info: Info, note_id: int
    ) -> Optional[GQLNote]:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401, detail="Unauthorized"
            )

        service = NoteService(get_db_from_context(info))
        result = service.get_note(note_id, user.id)
        if result:
            return GQLNote.from_domain(result)
        return None

    @strawberry.field(
        description="List all notes for the current user"
    )
    def list_notes(
        self, info: Info, page: int = 1, size: int = 50
    ) -> List[GQLNote]:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401, detail="Unauthorized"
            )

        service = NoteService(get_db_from_context(info))
        result = service.list_notes(user.id, page, size)
        return [
            GQLNote.from_domain(item)
            for item in result["items"]
        ]

    @strawberry.field(description="Get a Task by ID")
    def get_task(
        self, info: Info, task_id: int
    ) -> Optional[Task]:
        """Get a task by ID.

        Args:
            info: GraphQL request info
            task_id: Task ID

        Returns:
            Task if found, None otherwise

        Raises:
            HTTPException: If user is not authenticated
        """
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to get task",
            )

        service = TaskService(get_db_from_context(info))
        try:
            result = service.get_task(task_id, user.id)
            return (
                Task.from_domain(result) if result else None
            )
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found: {str(e)}",
            )

    @strawberry.field(description="List all Tasks")
    def list_tasks(
        self,
        info: Info,
        page: int = 1,
        size: int = 50,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
    ) -> TaskConnection:
        """List all tasks for the current user.

        Args:
            info: GraphQL request info
            page: Page number (1-based)
            size: Items per page
            status: Filter by task status
            priority: Filter by task priority

        Returns:
            Paginated list of tasks

        Raises:
            HTTPException: If user is not authenticated
        """
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to list tasks",
            )

        service = TaskService(get_db_from_context(info))
        tasks = service.list_tasks(
            user_id=user.id,
            page=page,
            size=size,
            status=status,
            priority=priority,
        )

        return TaskConnection(
            items=[
                Task.from_domain(task)
                for task in tasks["items"]
            ],
            total=tasks["total"],
            page=tasks["page"],
            size=tasks["size"],
        )

    @strawberry.field(description="Get subtasks for a task")
    def get_subtasks(
        self,
        info: Info,
        task_id: int,
        page: int = 1,
        size: int = 50,
    ) -> TaskConnection:
        """Get subtasks for a specific task.

        Args:
            info: GraphQL request info
            task_id: Parent task ID
            page: Page number (1-based)
            size: Items per page

        Returns:
            Paginated list of subtasks

        Raises:
            HTTPException: If user is not authenticated or task not found
        """
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to get subtasks",
            )

        service = TaskService(get_db_from_context(info))
        try:
            tasks = service.list_tasks(
                user_id=user.id,
                parent_id=task_id,
                page=page,
                size=size,
            )
            return TaskConnection(
                items=[
                    Task.from_domain(task)
                    for task in tasks["items"]
                ],
                total=tasks["total"],
                page=tasks["page"],
                size=tasks["size"],
            )
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found: {str(e)}",
            )
