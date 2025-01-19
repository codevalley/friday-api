#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

# Create a log file
LOG_FILE="test_flow.log"
echo "Starting test flow at $(date)" > $LOG_FILE

# Get current date in ISO format and add days
get_future_date() {
    local days=$1
    date -u -v+${days}d "+%Y-%m-%dT%H:%M:%SZ"
}

echo -e "${BLUE}Starting test flow...${NC}"

# parse optional argument for the API base URL
# if nothing provided, use http://localhost:8000/v1
BASE_URL="${1:-"http://localhost:8000/v1"}"
echo "Using base URL: $BASE_URL" >> $LOG_FILE

# Initialize database
echo -e "\n${BLUE}Initializing database...${NC}"
mysql -u root -p$DATABASE_PASSWORD $DATABASE_NAME < scripts/init_database.sql
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to initialize database${NC}"
    exit 1
fi
echo -e "${GREEN}Database initialized successfully${NC}"

# Function to extract value from JSON response
# Usage: extract_json_value "response" "field"
extract_json_value() {
    local response=$1
    local field=$2

    # First try to extract from data field (GenericResponse format)
    # This handles nested fields like data.id, data.items, etc.
    value=$(echo "$response" | grep -o "\"data\":{[^}]*\"$field\":\"[^\"]*\"" | grep -o "\"$field\":\"[^\"]*\"" | sed -E "s/\"$field\":\"//;s/\"$//")

    # If not found in data field, try direct field (for backward compatibility)
    if [ -z "$value" ]; then
        value=$(echo "$response" | grep -o "\"$field\":\"[^\"]*\"" | sed -E "s/\"$field\":\"//;s/\"$//")
    fi

    # If still not found, try for non-string values
    if [ -z "$value" ]; then
        value=$(echo "$response" | grep -o "\"data\":{[^}]*\"$field\":[^,}]*" | grep -o "\"$field\":[^,}]*" | sed -E "s/\"$field\"://;s/\"//g")
        if [ -z "$value" ]; then
            value=$(echo "$response" | grep -o "\"$field\":[^,}]*" | sed -E "s/\"$field\"://;s/\"//g")
        fi
    fi

    # Trim any whitespace
    value=$(echo "$value" | sed -E 's/^[[:space:]]*|[[:space:]]*$//g')

    echo "$value"
}

# Function to check API response
check_api_response() {
    local response=$1
    local context=$2

    # Check for error response with non-null error field
    if echo "$response" | grep -q "\"error\":[^n]"; then
        echo -e "${RED}✗ Failed - $context${NC}"
        echo "$response"
        return 1
    fi

    # Check for data field (GenericResponse format)
    if echo "$response" | grep -q "\"data\":{"; then
        echo -e "${GREEN}✓ Success${NC}"
        return 0
    fi

    # Special case for auth endpoints that might not be wrapped yet
    if echo "$response" | grep -q "\"user_secret\":\|\"access_token\":"; then
        echo -e "${GREEN}✓ Success${NC}"
        return 0
    fi

    # Special case for MessageResponse format
    if echo "$response" | grep -q "\"message\":"; then
        echo -e "${GREEN}✓ Success${NC}"
        return 0
    fi

    echo -e "${RED}✗ Failed - $context - Invalid response format${NC}"
    echo "$response"
    return 1
}

# Function to wait for activity processing
wait_for_activity_processing() {
    local activity_id=$1
    local token=$2
    local max_attempts=30
    local attempt=1
    local status=""

    echo -e "\n${BLUE}Waiting for activity $activity_id to be processed...${NC}"

    while [ $attempt -le $max_attempts ]; do
        local response=$(curl -s -X GET "$BASE_URL/activities/$activity_id" \
            -H "Authorization: Bearer $token")
        echo "Raw response: $response"  # Debug line
        status=$(extract_json_value "$response" "processing_status")
        echo "Extracted status: '$status'"  # Debug line with quotes

        case "$status" in
            "completed")
                echo -e "${GREEN}Activity processing completed successfully${NC}"
                return 0
                ;;
            "failed")
                echo -e "${RED}Activity processing failed${NC}"
                return 1
                ;;
            "processing")
                echo "Processing status: $status (attempt $attempt/$max_attempts)"
                ;;
            "pending"|"not_processed")
                echo "Waiting for processing to start... (attempt $attempt/$max_attempts)"
                ;;
            *)
                echo "Unknown status: $status (attempt $attempt/$max_attempts)"
                ;;
        esac

        sleep 1
        attempt=$((attempt + 1))
    done

    echo -e "${RED}Activity processing timed out after $max_attempts attempts${NC}"
    return 1
}

# Store responses in variables for better JSON handling
READING_SCHEMA='{
    "type": "object",
    "properties": {
        "book": { "type": "string" },
        "pages": { "type": "number" }
    },
    "required": ["book", "pages"]
}'

EXERCISE_SCHEMA='{
    "type": "object",
    "properties": {
        "type": { "type": "string" },
        "duration": { "type": "number" }
    },
    "required": ["type", "duration"]
}'

CODING_SCHEMA='{
    "type": "object",
    "properties": {
        "language": { "type": "string" },
        "hours": { "type": "number" }
    },
    "required": ["language", "hours"]
}'

# 1. Create first user
echo -e "\n${BLUE}1. Creating first user (user1)...${NC}"
USER1_RESPONSE=$(curl -s -S -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user1"
    }' 2>> $LOG_FILE)
USER1_API_KEY=$(extract_json_value "$USER1_RESPONSE" "user_secret")
echo "User1 Response: $USER1_RESPONSE"
echo "User1 API Key: $USER1_API_KEY"
check_api_response "$USER1_RESPONSE" "User registration"

# Get token for user1
echo -e "\n${BLUE}Getting token for user1...${NC}"
TOKEN1_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_secret\": \"$USER1_API_KEY\"
    }")
TOKEN1=$(extract_json_value "$TOKEN1_RESPONSE" "access_token")
echo "Token Response: $TOKEN1_RESPONSE"
echo "Token: $TOKEN1"
check_api_response "$TOKEN1_RESPONSE" "Token generation"

# 2. Create activities for user1
echo -e "\n${BLUE}2. Creating activities for user1...${NC}"
# Activity 1: Reading
ACTIVITY1_RESPONSE=$(curl -s -X POST "$BASE_URL/activities" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Reading\",
        \"description\": \"Track reading sessions\",
        \"activity_schema\": $READING_SCHEMA,
        \"icon\": \"📚\",
        \"color\": \"#4A90E2\"
    }")
echo "Activity1 Response: $ACTIVITY1_RESPONSE"
if check_api_response "$ACTIVITY1_RESPONSE" "Creating reading activity"; then
    ACTIVITY1_ID=$(extract_json_value "$ACTIVITY1_RESPONSE" "id")
    echo "Activity1 ID (raw): '$ACTIVITY1_ID'"  # Debug output with quotes
    if [ ! -z "$ACTIVITY1_ID" ]; then
        wait_for_activity_processing "$ACTIVITY1_ID" "$TOKEN1"
    else
        echo -e "${RED}Failed to extract activity ID${NC}"
        exit 1
    fi
else
    echo -e "${RED}Failed to create activity${NC}"
    exit 1
fi

# Activity 2: Exercise
ACTIVITY2_RESPONSE=$(curl -s -X POST "$BASE_URL/activities" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Exercise\",
        \"description\": \"Track workouts\",
        \"activity_schema\": $EXERCISE_SCHEMA,
        \"icon\": \"💪\",
        \"color\": \"#FF5733\"
    }")
echo "Activity2 Response: $ACTIVITY2_RESPONSE"
if check_api_response "$ACTIVITY2_RESPONSE" "Creating exercise activity"; then
    ACTIVITY2_ID=$(extract_json_value "$ACTIVITY2_RESPONSE" "id")
    echo "Activity2 ID (raw): '$ACTIVITY2_ID'"  # Debug output with quotes
    if [ ! -z "$ACTIVITY2_ID" ]; then
        wait_for_activity_processing "$ACTIVITY2_ID" "$TOKEN1"
    else
        echo -e "${RED}Failed to extract activity ID${NC}"
        exit 1
    fi
else
    echo -e "${RED}Failed to create activity${NC}"
    exit 1
fi

# Verify activity IDs
if [ -z "$ACTIVITY1_ID" ] || [ -z "$ACTIVITY2_ID" ]; then
    echo -e "${RED}Failed to extract activity IDs${NC}"
    echo "Activity1 ID: '$ACTIVITY1_ID'"
    echo "Activity2 ID: '$ACTIVITY2_ID'"
    exit 1
fi

# 3. Create moments for user1
echo -e "\n${BLUE}3. Creating moments for user1...${NC}"
# Reading moments
for i in {1..2}; do
    echo "Creating reading moment $i with activity ID: $ACTIVITY1_ID"
    MOMENT_DATA="{\"book\":\"Book $i\",\"pages\":$((i * 50))}"
    MOMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/moments" \
        -H "Authorization: Bearer $TOKEN1" \
        -H "Content-Type: application/json" \
        -d "{
            \"activity_id\": $ACTIVITY1_ID,
            \"data\": $MOMENT_DATA,
            \"timestamp\": \"2024-12-12T$((12 + i)):30:00Z\"
        }")
    echo "Reading Moment $i Response: $MOMENT_RESPONSE"
    check_api_response "$MOMENT_RESPONSE" "Creating reading moment $i"
done

# Exercise moments
for i in {1..2}; do
    echo "Creating exercise moment $i with activity ID: $ACTIVITY2_ID"
    MOMENT_DATA="{\"type\":\"Running\",\"duration\":$((i * 30))}"
    MOMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/moments" \
        -H "Authorization: Bearer $TOKEN1" \
        -H "Content-Type: application/json" \
        -d "{
            \"activity_id\": $ACTIVITY2_ID,
            \"data\": $MOMENT_DATA,
            \"timestamp\": \"2024-12-12T$((14 + i)):30:00Z\"
        }")
    echo "Exercise Moment $i Response: $MOMENT_RESPONSE"
    check_api_response "$MOMENT_RESPONSE" "Creating exercise moment $i"
done

# 4. Create second user
echo -e "\n${BLUE}4. Creating second user (user2)...${NC}"
USER2_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user2"
    }')
USER2_API_KEY=$(extract_json_value "$USER2_RESPONSE" "user_secret")
echo "User2 Response: $USER2_RESPONSE"
echo "User2 API Key: $USER2_API_KEY"
check_api_response "$USER2_RESPONSE" "User2 registration"

# Get token for user2
echo -e "\n${BLUE}Getting token for user2...${NC}"
TOKEN2_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_secret\": \"$USER2_API_KEY\"
    }")
TOKEN2=$(extract_json_value "$TOKEN2_RESPONSE" "access_token")
echo "Token2 Response: $TOKEN2_RESPONSE"
echo "Token2: $TOKEN2"
check_api_response "$TOKEN2_RESPONSE" "Token2 generation"

# 5. Create activity for user2
echo -e "\n${BLUE}5. Creating activity for user2...${NC}"
ACTIVITY3_RESPONSE=$(curl -s -X POST "$BASE_URL/activities" \
    -H "Authorization: Bearer $TOKEN2" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Coding\",
        \"description\": \"Track coding sessions\",
        \"activity_schema\": $CODING_SCHEMA,
        \"icon\": \"💻\",
        \"color\": \"#2ECC71\"
    }")
ACTIVITY3_ID=$(extract_json_value "$ACTIVITY3_RESPONSE" "id")
echo "Activity3 Response: $ACTIVITY3_RESPONSE"
echo "Activity3 ID: $ACTIVITY3_ID"
check_api_response "$ACTIVITY3_RESPONSE" "Creating coding activity"

# 6. Create moments for user2
echo -e "\n${BLUE}6. Creating moments for user2...${NC}"
for i in {1..3}; do
    MOMENT_DATA="{\"language\":\"Python\",\"hours\":$i}"
    MOMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/moments" \
        -H "Authorization: Bearer $TOKEN2" \
        -H "Content-Type: application/json" \
        -d "{
            \"activity_id\": $ACTIVITY3_ID,
            \"data\": $MOMENT_DATA,
            \"timestamp\": \"2024-12-12T$((16 + i)):30:00Z\"
        }")
    echo "Coding Moment $i Response: $MOMENT_RESPONSE"
    check_api_response "$MOMENT_RESPONSE" "Creating coding moment $i"
done

# 7. List activities for user2 (should only see their own)
echo -e "\n${BLUE}7. Listing activities for user2...${NC}"
ACTIVITIES_RESPONSE=$(curl -s -X GET "$BASE_URL/activities?page=1&size=100" \
    -H "Authorization: Bearer $TOKEN2")
echo "Activities Response: $ACTIVITIES_RESPONSE"
check_api_response "$ACTIVITIES_RESPONSE" "Listing activities"

# 8. List moments for user2 (should only see their own)
echo -e "\n${BLUE}8. Listing moments for user2...${NC}"
MOMENTS_RESPONSE=$(curl -s -X GET "$BASE_URL/moments?page=1&size=50" \
    -H "Authorization: Bearer $TOKEN2")
echo "Moments Response: $MOMENTS_RESPONSE"
check_api_response "$MOMENTS_RESPONSE" "Listing moments"

# 9. Switch back to user1 and get specific activity
echo -e "\n${BLUE}9. Getting specific activity for user1...${NC}"
ACTIVITY_RESPONSE=$(curl -s -X GET "$BASE_URL/activities/$ACTIVITY1_ID" \
    -H "Authorization: Bearer $TOKEN1")
echo "Activity Response: $ACTIVITY_RESPONSE"
check_api_response "$ACTIVITY_RESPONSE" "Getting specific activity"

# 10. Get specific moment for user1
echo -e "\n${BLUE}10. Getting specific moment for user1...${NC}"
MOMENT_RESPONSE=$(curl -s -X GET "$BASE_URL/moments/1" \
    -H "Authorization: Bearer $TOKEN1")
echo "Moment Response: $MOMENT_RESPONSE"
check_api_response "$MOMENT_RESPONSE" "Getting specific moment"

# 11. Create notes for user1
echo -e "\n${BLUE}11. Creating notes for user1...${NC}"
# Note with text only
NOTE1_RESPONSE=$(curl -s -X POST "$BASE_URL/notes" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "My first note - text only"
    }')
echo "Note1 Response: $NOTE1_RESPONSE"
NOTE1_ID=$(extract_json_value "$NOTE1_RESPONSE" "id")
check_api_response "$NOTE1_RESPONSE" "Creating text-only note"

# Note with photo attachment
NOTE2_RESPONSE=$(curl -s -X POST "$BASE_URL/notes" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "My second note - with photo",
        "attachment_url": "https://example.com/photo.jpg",
        "attachment_type": "image"
    }')
echo "Note2 Response: $NOTE2_RESPONSE"
NOTE2_ID=$(extract_json_value "$NOTE2_RESPONSE" "id")
check_api_response "$NOTE2_RESPONSE" "Creating note with photo"

# 12. Create notes for user2
echo -e "\n${BLUE}12. Creating notes for user2...${NC}"
# Note with voice attachment
NOTE3_RESPONSE=$(curl -s -X POST "$BASE_URL/notes" \
    -H "Authorization: Bearer $TOKEN2" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "Voice note from user2",
        "attachment_url": "https://example.com/voice.mp3",
        "attachment_type": "document"
    }')
echo "Note3 Response: $NOTE3_RESPONSE"
NOTE3_ID=$(extract_json_value "$NOTE3_RESPONSE" "id")
check_api_response "$NOTE3_RESPONSE" "Creating note with voice attachment"

# 13. List notes for user1
echo -e "\n${BLUE}13. Listing notes for user1...${NC}"
NOTES_RESPONSE=$(curl -s -X GET "$BASE_URL/notes?page=1&size=50" \
    -H "Authorization: Bearer $TOKEN1")
echo "Notes Response: $NOTES_RESPONSE"
check_api_response "$NOTES_RESPONSE" "Listing notes for user1"

# 14. Update note for user1
echo -e "\n${BLUE}14. Updating note for user1...${NC}"
UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/notes/$NOTE1_ID" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "Updated first note content"
    }')
echo "Update Response: $UPDATE_RESPONSE"
check_api_response "$UPDATE_RESPONSE" "Updating note"

# 15. Try to access user2's note with user1's token (should fail)
echo -e "\n${BLUE}15. Testing note access control...${NC}"
UNAUTHORIZED_RESPONSE=$(curl -s -X GET "$BASE_URL/notes/$NOTE3_ID" \
    -H "Authorization: Bearer $TOKEN1")
echo "Unauthorized Response: $UNAUTHORIZED_RESPONSE"
if echo "$UNAUTHORIZED_RESPONSE" | grep -q "\"detail\":\"Note not found\""; then
    echo -e "${GREEN}✓ Access control working correctly${NC}"
else
    echo -e "${RED}✗ Access control test failed${NC}"
    exit 1
fi

# 16. Delete note for user1
echo -e "\n${BLUE}16. Deleting note for user1...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/notes/$NOTE2_ID" \
    -H "Authorization: Bearer $TOKEN1")
echo "Delete Response: $DELETE_RESPONSE"
check_api_response "$DELETE_RESPONSE" "Deleting note"

# Verify deletion
VERIFY_DELETE_RESPONSE=$(curl -s -X GET "$BASE_URL/notes/$NOTE2_ID" \
    -H "Authorization: Bearer $TOKEN1")
if echo "$VERIFY_DELETE_RESPONSE" | grep -q "\"detail\":\"Note not found\""; then
    echo -e "${GREEN}✓ Note deletion verified${NC}"
else
    echo -e "${RED}✗ Note deletion verification failed${NC}"
    exit 1
fi

# 17. Create tasks for user1
echo -e "\n${BLUE}17. Creating tasks for user1...${NC}"
# Task with just title and description
TASK1_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "First Task",
        "description": "This is a simple task",
        "status": "todo",
        "priority": "medium",
        "due_date": "'$(get_future_date 30)'",
        "tags": ["test", "simple"]
    }')
echo "Task1 Response: $TASK1_RESPONSE"
TASK1_ID=$(extract_json_value "$TASK1_RESPONSE" "id")
check_api_response "$TASK1_RESPONSE" "Creating simple task"

# Task with all fields
TASK2_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Second Task",
        "description": "This is a complex task",
        "status": "in_progress",
        "priority": "high",
        "due_date": "'$(get_future_date 15)'",
        "tags": ["test", "complex"],
        "parent_id": '"$TASK1_ID"'
    }')
echo "Task2 Response: $TASK2_RESPONSE"
TASK2_ID=$(extract_json_value "$TASK2_RESPONSE" "id")
check_api_response "$TASK2_RESPONSE" "Creating complex task"

# Create topics for user1
echo -e "\n${BLUE}Creating topics for user1...${NC}"
# Work topic
TOPIC1_RESPONSE=$(curl -s -X POST "$BASE_URL/topics" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Work",
        "icon": "💼"
    }')
echo "Topic1 Response: $TOPIC1_RESPONSE"
TOPIC1_ID=$(extract_json_value "$TOPIC1_RESPONSE" "id")
check_api_response "$TOPIC1_RESPONSE" "Creating work topic"

# Personal topic
TOPIC2_RESPONSE=$(curl -s -X POST "$BASE_URL/topics" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Personal",
        "icon": "🏠"
    }')
echo "Topic2 Response: $TOPIC2_RESPONSE"
TOPIC2_ID=$(extract_json_value "$TOPIC2_RESPONSE" "id")
check_api_response "$TOPIC2_RESPONSE" "Creating personal topic"

# Update tasks with topics
echo -e "\n${BLUE}Updating tasks with topics...${NC}"
# Update first task with Work topic
UPDATE_TASK1_RESPONSE=$(curl -s -X PUT "$BASE_URL/tasks/$TASK1_ID" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "topic_id": '"$TOPIC1_ID"'
    }')
echo "Update Task1 Response: $UPDATE_TASK1_RESPONSE"
check_api_response "$UPDATE_TASK1_RESPONSE" "Updating task1 with topic"

# Update second task with Personal topic
UPDATE_TASK2_RESPONSE=$(curl -s -X PUT "$BASE_URL/tasks/$TASK2_ID" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "topic_id": '"$TOPIC2_ID"'
    }')
echo "Update Task2 Response: $UPDATE_TASK2_RESPONSE"
check_api_response "$UPDATE_TASK2_RESPONSE" "Updating task2 with topic"

# List tasks by topic
echo -e "\n${BLUE}Listing tasks by topic...${NC}"
# Get tasks for Work topic
WORK_TASKS_RESPONSE=$(curl -s -X GET "$BASE_URL/topics/$TOPIC1_ID/tasks" \
    -H "Authorization: Bearer $TOKEN1")
echo "Work Tasks Response: $WORK_TASKS_RESPONSE"
check_api_response "$WORK_TASKS_RESPONSE" "Listing work tasks"

# Get tasks for Personal topic
PERSONAL_TASKS_RESPONSE=$(curl -s -X GET "$BASE_URL/topics/$TOPIC2_ID/tasks" \
    -H "Authorization: Bearer $TOKEN1")
echo "Personal Tasks Response: $PERSONAL_TASKS_RESPONSE"
check_api_response "$PERSONAL_TASKS_RESPONSE" "Listing personal tasks"

# 18. Create tasks for user2
echo -e "\n${BLUE}18. Creating tasks for user2...${NC}"
TASK3_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks" \
    -H "Authorization: Bearer $TOKEN2" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "User2 Task",
        "description": "Task for user2",
        "status": "todo",
        "priority": "low",
        "due_date": "'$(get_future_date 7)'",
        "tags": ["user2"]
    }')
echo "Task3 Response: $TASK3_RESPONSE"
TASK3_ID=$(extract_json_value "$TASK3_RESPONSE" "id")
check_api_response "$TASK3_RESPONSE" "Creating task for user2"

# 19. List tasks for user1
echo -e "\n${BLUE}19. Listing tasks for user1...${NC}"
TASKS_RESPONSE=$(curl -s -X GET "$BASE_URL/tasks?page=1&size=50" \
    -H "Authorization: Bearer $TOKEN1")
echo "Tasks Response: $TASKS_RESPONSE"
check_api_response "$TASKS_RESPONSE" "Listing tasks for user1"

# 20. Update task for user1
echo -e "\n${BLUE}20. Updating task for user1...${NC}"
UPDATE_TASK_RESPONSE=$(curl -s -X PUT "$BASE_URL/tasks/$TASK1_ID" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Updated First Task",
        "status": "in_progress",
        "priority": "high"
    }')
echo "Update Task Response: $UPDATE_TASK_RESPONSE"
check_api_response "$UPDATE_TASK_RESPONSE" "Updating task"

# 21. Try to access user2's task with user1's token (should fail)
echo -e "\n${BLUE}21. Testing task access control...${NC}"
UNAUTHORIZED_TASK_RESPONSE=$(curl -s -X GET "$BASE_URL/tasks/$TASK3_ID" \
    -H "Authorization: Bearer $TOKEN1")
echo "Unauthorized Task Response: $UNAUTHORIZED_TASK_RESPONSE"
if echo "$UNAUTHORIZED_TASK_RESPONSE" | grep -q "\"detail\":\"Task not found\""; then
    echo -e "${GREEN}✓ Task access control working correctly${NC}"
else
    echo -e "${RED}✗ Task access control test failed${NC}"
    exit 1
fi

# 22. Delete task for user1
echo -e "\n${BLUE}22. Deleting task for user1...${NC}"
DELETE_TASK_RESPONSE=$(curl -s -X DELETE "$BASE_URL/tasks/$TASK2_ID" \
    -H "Authorization: Bearer $TOKEN1")
echo "Delete Task Response: $DELETE_TASK_RESPONSE"
check_api_response "$DELETE_TASK_RESPONSE" "Deleting task"

# Verify task deletion
VERIFY_TASK_DELETE_RESPONSE=$(curl -s -X GET "$BASE_URL/tasks/$TASK2_ID" \
    -H "Authorization: Bearer $TOKEN1")
if echo "$VERIFY_TASK_DELETE_RESPONSE" | grep -q "\"detail\":\"Task not found\""; then
    echo -e "${GREEN}✓ Task deletion verified${NC}"
else
    echo -e "${RED}✗ Task deletion verification failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}Test flow completed!${NC}"

echo -e "\n${BLUE}Test logs have been saved to $LOG_FILE${NC}"
