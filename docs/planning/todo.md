# Friday API todo

---

### **Recommended Epics & Tasks**

#### **Epic 1: Improve Code Consistency**
- **Task 1.1:** Standardize naming conventions across schemas (e.g., `activity_schema` vs. `activitySchema`).
- **Task 1.2:** Centralize validation logic in utilities (e.g., `_validate_pagination`).

#### **Epic 2: Enhance Error Handling**
- **Task 2.1:** Introduce a global exception handler for common errors like `ValidationError` or `SQLAlchemyError`.
- **Task 2.2:** Ensure repositories do not raise HTTP-specific exceptions.

#### **Epic 3: Optimize Performance**
- **Task 3.1:** Index JSON fields (`data`, `activity_schema`) or move heavily queried data to relational columns.
- **Task 3.2:** Profile database queries for the `list_moments` method to identify potential bottlenecks.

#### **Epic 4: Expand Test Coverage**
- **Task 4.1:** Add edge case tests for all service methods.
- **Task 4.2:** Implement integration tests for all endpoints, especially GraphQL queries and mutations.

#### **Epic 6: Strengthen Security**
- **Task 6.1:** Ensure consistent use of `bcrypt` or a similar library for hashing secrets.
- **Task 6.2:** Validate JWT expiration logic for long-running sessions.

#### **Epic 7: Improve Documentation**
- **Task 7.1:** Update API and GraphQL documentation to reflect any changes in naming conventions.
- **Task 7.2:** Add examples for using the JSON schema validation in custom activities.

#### **Epic 8: Simplify GraphQL Logic**
- **Task 8.1:** Leverage GraphQL resolvers for field-level optimizations.
- **Task 8.2:** Remove redundant service calls in GraphQL queries.

---

Would you like me to organize this into a Kanban-style format or prioritize these epics and tasks further? Let me know how you'd like to proceed!
