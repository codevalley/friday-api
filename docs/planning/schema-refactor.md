# Project Plan: Refactoring Note, Moment, Task Relationships

## Development Workflow
1. Pick the next incomplete task from the plan (tasks are ordered by dependency)
2. Implement the task following the established patterns from Notes/Moments/Activities
3. Write tests before or alongside the implementation (TDD preferred)
4. Mark the task as complete (✓) and add implementation details/comments
5. Run all tests to ensure no regressions
6. Move to the next task

## Overview
The plan of this refactoring is to make the `Note` entity a leaf node, and have `Moment` and `Task` each optionally reference a `Note`. This will simplify the data model and make it more consistent with the existing patterns for Notes, Moments, and Activities.

A Note is a "leaf" from a DB perspective, which other entities might point to, but it doesn't store references back. Activities are also a sort of "type reference," not referencing anything else. Moments always reference an Activity and optionally a Note. Tasks optionally reference a parent Task or a single Note.

## Epic 1: Model & Schema Changes

**Goal**: Update the ORM, domain models, and DB schema so that `Note` does not store `activity_id`/`moment_id`, but `Moment` and `Task` each have an optional `note_id`.

### Task 1.1: Database Schema & Migrations ✓
1. **Remove** `activity_id` and `moment_id` columns from the `notes` table. ✓
2. **Add** `note_id` column to `moments` table (`moment_id` → `notes`) – optional (`nullable=True`). ✓
3. **Add** `note_id` column to `tasks` table – optional (`nullable=True`). ✓
4. Ensure referential constraints (foreign keys) are properly set: ✓
   - `moments.note_id → notes.id` ✓
   - `tasks.note_id → notes.id` ✓
5. Update init_database.sql with the new schema ✓

Implementation details:
- Updated `init_database.sql` to create tables in the correct order (notes before moments/tasks)
- Added `ON DELETE SET NULL` for note references to ensure safe deletion
- Added appropriate indexes for `note_id` columns
- Removed old note references and constraints

### Task 1.2: Update ORM Models ✓
1. **`NoteModel`**: ✓
   - Remove `activity_id` and `moment_id` columns from `Note`. ✓
   - Remove relationships referencing `Activity` or `Moment`. ✓
   - Add back-reference relationship to moments ✓
2. **`MomentModel`**: ✓
   - Add `note_id` column (SQLAlchemy `Column(Integer, ForeignKey("notes.id"))`). ✓
   - Add `note` relationship: one-way optional relationship to Note. ✓
   - Fix relationship with User model to use consistent naming ✓
3. **`TaskModel`**: ✓
   - Add `note_id` column and `note` relationship. ✓
4. Keep Note as a pure leaf node (no back-references). ✓

Implementation details:
- Used SQLAlchemy's `Mapped` types for better type safety
- Added comprehensive tests for all relationships
- Ensured proper cascade behavior on deletions
- Added tests for optional nature of relationships
- Fixed relationship naming consistency between models
- Added proper back-references for all relationships
- Ensured proper ondelete behavior for foreign keys

### Task 1.3: Domain Layer Adjustments ✓
1. **`NoteData`**: remove any fields referencing `activity_id` or `moment_id`. ✓
2. **`MomentData`**: add optional `note_id: Optional[int]` and `note: Optional[NoteData]`. ✓
3. **`TaskData`**: add optional `note_id: Optional[int]` and `note: Optional[NoteData]`. ✓
4. Where domain logic references "Note → Activity" or "Note → Moment," remove or refactor. ✓

Implementation details:
- Updated domain models to reflect new relationships
- Added validation for note_id fields (must be positive integers when present)
- Added tests for all new fields and validation rules
- Updated conversion methods (to_dict, from_dict) to handle note references
- Added support for both snake_case and camelCase in from_dict methods
- Added comprehensive test suites for all domain models

---

## Epic 2: Refactor Services & Repositories

**Goal**: Ensure that the changed relationships are handled consistently in the code (creation, updates, queries).

### Task 2.1: Repositories
1. **`NoteRepository`**: ✓
   - Remove references to `activity_id` or `moment_id`. ✓
   - Possibly remove the notion of "Note referencing an Activity or Moment." ✓
2. **`MomentRepository`**: ✓
   - On creation, if a `note_id` is provided, set it. ✓
   - If we do "get moments for a note," add a new query if needed, or remove existing code that used `Note.moment_id`. ✓
3. **`TaskRepository`**: ✓
   - On creation or update, if `note_id` is provided, set it. ✓
   - If we want "tasks for a note," similarly handle it. ✓

Implementation details:
- Updated repository methods to handle new relationship structure
- Added validation for note_id references
- Ensured proper error handling for invalid references
- Added tests for all new repository methods
- Fixed circular import issues between models

### Task 2.2: Service Logic
1. **`NoteService`**: ✓
   - Remove logic that references `activity_id` or `moment_id` in a `Note`. ✓
   - If you had code that "attach a note to a moment," switch that to "update the `moment.note_id` in the `MomentService`." ✓
2. **`MomentService`**: ✓
   - If user wants to attach a note to a moment, do `moment.note_id = that_note.id`. ✓
   - Validate that the note is valid, that the user can see it, etc. ✓
3. **`TaskService`**: ✓
   - If user wants to attach a note to a task, do `task.note_id = that_note.id`. ✓

Implementation details:
- Updated service methods to handle new relationship structure
- Added validation for note attachments
- Added proper error handling for invalid operations
- Added tests for all new service methods
- Fixed circular dependencies between services

**Sub-tasks**: ✓
- Adjust or remove any code in `NoteService` that was creating `Note` with `moment_id` or `activity_id`. ✓
- Possibly add new methods in `MomentService` / `TaskService` to "attach a note" or "detach a note." ✓

---

## Epic 3: Clean Up Routers & Schemas ✓

**Goal**: Ensure that the new relationships are consistent at the API layer.

### Task 3.1: REST Endpoints ✓
- **`NoteRouter`**: ✓
  - Remove parameters that let you directly specify `activity_id` or `moment_id` when creating a note. ✓
- **`MomentRouter`**: ✓
  - Added endpoints to associate a note with a moment (`PUT /moments/{moment_id}/note` and `DELETE /moments/{moment_id}/note`). ✓
- **`TaskRouter`**: ✓
  - Added endpoints to set or update `note_id` (`PUT /tasks/{task_id}/note` and `DELETE /tasks/{task_id}/note`). ✓

Implementation details:
- Added comprehensive validation in note attachment endpoints
- Ensured proper error handling for invalid note IDs
- Added ownership validation for all operations
- Added proper documentation for all new endpoints
- Maintained consistent response formats
- Added proper authorization checks for all operations

---

## Epic 4: Testing & Validation

**Goal**: Ensure existing functionality keeps working, and new references (Task ↔ Note, Moment ↔ Note) are correct.

### Task 4.1: Unit & Integration Tests
1. Write or update tests for:
   - **Creating a Note** (no references to moment/task).
   - **Attaching a Note** to a moment or task.
   - **Detaching** a note or reassigning a note, if relevant.
2. Check old routes that used to create a note with `moment_id` or `activity_id`; make sure to refactor or remove them.

### Task 4.2: Data Migration Testing
- If you have existing data in production, test the migrations carefully.
- Possibly do a zero-downtime approach or a two-phase migration if needed.

---

## Epic 5: Documentation & Cleanup

**Goal**: Document new relationships, remove any stale references.

### Task 5.1: Documentation
- Update system architecture diagrams to reflect that `Moment` and `Task` reference `Note`, not the other way around.
- Document the new ways to attach a note to a moment or a task.

### Task 5.2: Code Cleanup
- Remove or rename any references (like old methods or old columns) that might confuse future developers.
