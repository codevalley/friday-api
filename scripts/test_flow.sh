#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
PURPLE='\033[0;35m'

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

    # Check if response is empty
    if [ -z "$response" ]; then
        echo -e "${RED}✗ Failed - Empty response from server${NC}"
        return 1
    fi

    # Check for error response with non-null error field
    if echo "$response" | grep -q "\"error\":[^n]"; then
        echo -e "${RED}✗ Failed - $context${NC}"
        echo "$response"
        return 1
    fi

    # Check for data field (GenericResponse format)
    if echo "$response" | grep -q "\"data\":{"; then
        return 0
    fi

    # Check for direct response format (items array at root level)
    if echo "$response" | grep -q "\"items\":\["; then
        return 0
    fi

    # Check for message-only response
    if echo "$response" | grep -q "\"message\":"; then
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

# Function to clean up storage directory
cleanup_storage() {
    echo -e "\n${BLUE}Cleaning up storage directory...${NC}"
    STORAGE_DIR="storage"
    if [ -d "$STORAGE_DIR" ]; then
        rm -rf "${STORAGE_DIR:?}/"*
        echo -e "${GREEN}✓ Storage directory cleaned${NC}"
    else
        echo -e "${YELLOW}Storage directory not found${NC}"
    fi
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

# Function to print API response with endpoint info
print_api_response() {
    local endpoint=$1
    local response=$2
    echo -e "\n${PURPLE}=== Raw API Response for ${endpoint} ===${NC}"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
    echo -e "${PURPLE}==============================${NC}\n"
}

# 1. Create first user
echo -e "\n${BLUE}1. Creating first user (user1)...${NC}"
USER1_RESPONSE=$(curl -s -S -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user1"
    }' 2>> $LOG_FILE)
print_api_response "/auth/register" "$USER1_RESPONSE"
USER1_API_KEY=$(extract_json_value "$USER1_RESPONSE" "user_secret")
echo "User1 API Key: $USER1_API_KEY"
check_api_response "$USER1_RESPONSE" "User registration"

# Get token for user1
echo -e "\n${BLUE}Getting token for user1...${NC}"
TOKEN1_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_secret\": \"$USER1_API_KEY\"
    }")
print_api_response "/auth/token" "$TOKEN1_RESPONSE"
TOKEN1=$(extract_json_value "$TOKEN1_RESPONSE" "access_token")
echo "Token: $TOKEN1"
check_api_response "$TOKEN1_RESPONSE" "Token generation"

# Check user1's profile
echo -e "\n${BLUE}Checking user1's profile...${NC}"
USER1_PROFILE_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/auth/me" "$USER1_PROFILE_RESPONSE"
check_api_response "$USER1_PROFILE_RESPONSE" "Getting user1 profile"
USER1_ID=$(extract_json_value "$USER1_PROFILE_RESPONSE" "id")
USER1_USERNAME=$(extract_json_value "$USER1_PROFILE_RESPONSE" "username")
USER1_CREATED=$(extract_json_value "$USER1_PROFILE_RESPONSE" "created_at")
USER1_UPDATED=$(extract_json_value "$USER1_PROFILE_RESPONSE" "updated_at")

echo -e "\n${GREEN}User Profile Details:${NC}"
echo -e "ID: ${USER1_ID}"
echo -e "Username: ${USER1_USERNAME}"
echo -e "Created: ${USER1_CREATED}"
echo -e "Last Updated: ${USER1_UPDATED}"

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
print_api_response "/activities (Reading)" "$ACTIVITY1_RESPONSE"
if check_api_response "$ACTIVITY1_RESPONSE" "Creating reading activity"; then
    ACTIVITY1_ID=$(extract_json_value "$ACTIVITY1_RESPONSE" "id")
    echo "Activity1 ID: $ACTIVITY1_ID"
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
print_api_response "/activities (Exercise)" "$ACTIVITY2_RESPONSE"
if check_api_response "$ACTIVITY2_RESPONSE" "Creating exercise activity"; then
    ACTIVITY2_ID=$(extract_json_value "$ACTIVITY2_RESPONSE" "id")
    echo "Activity2 ID: $ACTIVITY2_ID"
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
    print_api_response "/moments (Reading $i)" "$MOMENT_RESPONSE"
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
    print_api_response "/moments (Exercise $i)" "$MOMENT_RESPONSE"
    check_api_response "$MOMENT_RESPONSE" "Creating exercise moment $i"
done

# 4. Create second user
echo -e "\n${BLUE}4. Creating second user (user2)...${NC}"
USER2_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user2"
    }')
print_api_response "/auth/register" "$USER2_RESPONSE"
USER2_API_KEY=$(extract_json_value "$USER2_RESPONSE" "user_secret")
echo "User2 API Key: $USER2_API_KEY"
check_api_response "$USER2_RESPONSE" "User2 registration"

# Get token for user2
echo -e "\n${BLUE}Getting token for user2...${NC}"
TOKEN2_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_secret\": \"$USER2_API_KEY\"
    }")
print_api_response "/auth/token" "$TOKEN2_RESPONSE"
TOKEN2=$(extract_json_value "$TOKEN2_RESPONSE" "access_token")
echo "Token2: $TOKEN2"
check_api_response "$TOKEN2_RESPONSE" "Token2 generation"

# Check user2's profile
echo -e "\n${BLUE}Checking user2's profile...${NC}"
USER2_PROFILE_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $TOKEN2")
print_api_response "/auth/me" "$USER2_PROFILE_RESPONSE"
check_api_response "$USER2_PROFILE_RESPONSE" "Getting user2 profile"
USER2_ID=$(extract_json_value "$USER2_PROFILE_RESPONSE" "id")
USER2_USERNAME=$(extract_json_value "$USER2_PROFILE_RESPONSE" "username")
USER2_CREATED=$(extract_json_value "$USER2_PROFILE_RESPONSE" "created_at")
USER2_UPDATED=$(extract_json_value "$USER2_PROFILE_RESPONSE" "updated_at")

echo -e "\n${GREEN}User Profile Details:${NC}"
echo -e "ID: ${USER2_ID}"
echo -e "Username: ${USER2_USERNAME}"
echo -e "Created: ${USER2_CREATED}"
echo -e "Last Updated: ${USER2_UPDATED}"

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
print_api_response "/activities (Coding)" "$ACTIVITY3_RESPONSE"
ACTIVITY3_ID=$(extract_json_value "$ACTIVITY3_RESPONSE" "id")
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
    print_api_response "/moments (Coding $i)" "$MOMENT_RESPONSE"
    check_api_response "$MOMENT_RESPONSE" "Creating coding moment $i"
done

# 7. List activities for user2 (should only see their own)
echo -e "\n${BLUE}7. Listing activities for user2...${NC}"
ACTIVITIES_RESPONSE=$(curl -s -X GET "$BASE_URL/activities?page=1&size=100" \
    -H "Authorization: Bearer $TOKEN2")
print_api_response "/activities (List)" "$ACTIVITIES_RESPONSE"
check_api_response "$ACTIVITIES_RESPONSE" "Listing activities"

# 8. List moments for user2 (should only see their own)
echo -e "\n${BLUE}8. Listing moments for user2...${NC}"
MOMENTS_RESPONSE=$(curl -s -X GET "$BASE_URL/moments?page=1&size=50" \
    -H "Authorization: Bearer $TOKEN2")
print_api_response "/moments (List)" "$MOMENTS_RESPONSE"
check_api_response "$MOMENTS_RESPONSE" "Listing moments"

# 9. Switch back to user1 and get specific activity
echo -e "\n${BLUE}9. Getting specific activity for user1...${NC}"
ACTIVITY_RESPONSE=$(curl -s -X GET "$BASE_URL/activities/$ACTIVITY1_ID" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/activities/$ACTIVITY1_ID (Get)" "$ACTIVITY_RESPONSE"
check_api_response "$ACTIVITY_RESPONSE" "Getting specific activity"

# 10. Get specific moment for user1
echo -e "\n${BLUE}10. Getting specific moment for user1...${NC}"
MOMENT_RESPONSE=$(curl -s -X GET "$BASE_URL/moments/1" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/moments/1 (Get)" "$MOMENT_RESPONSE"
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
print_api_response "/notes (Text Only)" "$NOTE1_RESPONSE"
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
print_api_response "/notes (With Photo)" "$NOTE2_RESPONSE"
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
print_api_response "/notes (With Voice)" "$NOTE3_RESPONSE"
NOTE3_ID=$(extract_json_value "$NOTE3_RESPONSE" "id")
check_api_response "$NOTE3_RESPONSE" "Creating note with voice attachment"

# 13. List notes for user1
echo -e "\n${BLUE}13. Listing notes for user1...${NC}"
NOTES_RESPONSE=$(curl -s -X GET "$BASE_URL/notes?page=1&size=50" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/notes (List)" "$NOTES_RESPONSE"
check_api_response "$NOTES_RESPONSE" "Listing notes for user1"

# 14. Update note for user1
echo -e "\n${BLUE}14. Updating note for user1...${NC}"
UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/notes/$NOTE1_ID" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "Updated first note content"
    }')
print_api_response "/notes/$NOTE1_ID (Update)" "$UPDATE_RESPONSE"
check_api_response "$UPDATE_RESPONSE" "Updating note"

# 15. Try to access user2's note with user1's token (should fail)
echo -e "\n${BLUE}15. Testing note access control...${NC}"
UNAUTHORIZED_RESPONSE=$(curl -s -X GET "$BASE_URL/notes/$NOTE3_ID" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/notes/$NOTE3_ID (Unauthorized)" "$UNAUTHORIZED_RESPONSE"
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
print_api_response "/notes/$NOTE2_ID (Delete)" "$DELETE_RESPONSE"
check_api_response "$DELETE_RESPONSE" "Deleting note"

# Verify deletion
VERIFY_DELETE_RESPONSE=$(curl -s -X GET "$BASE_URL/notes/$NOTE2_ID" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/notes/$NOTE2_ID (Verify Delete)" "$VERIFY_DELETE_RESPONSE"
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
        "content": "Simple task that needs to be done",
        "status": "todo",
        "priority": "medium",
        "due_date": "'$(get_future_date 7)'",
        "tags": ["test", "simple"]
    }')
print_api_response "/tasks (Simple)" "$TASK1_RESPONSE"
TASK1_ID=$(extract_json_value "$TASK1_RESPONSE" "id")
check_api_response "$TASK1_RESPONSE" "Creating simple task"

# Task with all fields
TASK2_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "Complex task that requires multiple steps and careful planning. This task involves:\n1. Research phase\n2. Implementation\n3. Testing\n4. Documentation",
        "status": "in_progress",
        "priority": "high",
        "due_date": "'$(get_future_date 15)'",
        "tags": ["test", "complex"],
        "parent_id": '"$TASK1_ID"'
    }')
print_api_response "/tasks (Complex)" "$TASK2_RESPONSE"
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
        "content": "User2 task that needs to be completed by next week",
        "status": "todo",
        "priority": "low",
        "due_date": "'$(get_future_date 7)'",
        "tags": ["user2"]
    }')
print_api_response "/tasks (User2)" "$TASK3_RESPONSE"
TASK3_ID=$(extract_json_value "$TASK3_RESPONSE" "id")
check_api_response "$TASK3_RESPONSE" "Creating task for user2"

# 19. List tasks for user1
echo -e "\n${BLUE}19. Listing tasks for user1...${NC}"
TASKS_RESPONSE=$(curl -s -X GET "$BASE_URL/tasks?page=1&size=50" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/tasks (List)" "$TASKS_RESPONSE"
check_api_response "$TASKS_RESPONSE" "Listing tasks for user1"

# 20. Update task for user1
echo -e "\n${BLUE}20. Updating task for user1...${NC}"
UPDATE_TASK_RESPONSE=$(curl -s -X PUT "$BASE_URL/tasks/$TASK1_ID" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "content": "Updated first task content",
        "status": "in_progress",
        "priority": "high"
    }')
print_api_response "/tasks/$TASK1_ID (Update)" "$UPDATE_TASK_RESPONSE"
check_api_response "$UPDATE_TASK_RESPONSE" "Updating task"

# 21. Try to access user2's task with user1's token (should fail)
echo -e "\n${BLUE}21. Testing task access control...${NC}"
UNAUTHORIZED_TASK_RESPONSE=$(curl -s -X GET "$BASE_URL/tasks/$TASK3_ID" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/tasks/$TASK3_ID (Unauthorized)" "$UNAUTHORIZED_TASK_RESPONSE"
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
print_api_response "/tasks/$TASK2_ID (Delete)" "$DELETE_TASK_RESPONSE"
check_api_response "$DELETE_TASK_RESPONSE" "Deleting task"

# Verify task deletion
VERIFY_TASK_DELETE_RESPONSE=$(curl -s -X GET "$BASE_URL/tasks/$TASK2_ID" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/tasks/$TASK2_ID (Verify Delete)" "$VERIFY_TASK_DELETE_RESPONSE"
if echo "$VERIFY_TASK_DELETE_RESPONSE" | grep -q "\"detail\":\"Task not found\""; then
    echo -e "${GREEN}✓ Task deletion verified${NC}"
else
    echo -e "${RED}✗ Task deletion verification failed${NC}"
    exit 1
fi

# 23. Test document operations
echo -e "\n${BLUE}23. Testing document operations...${NC}"

# Create a private document for user1
echo -e "\n${BLUE}Creating private document for user1...${NC}"
PRIVATE_DOC_RESPONSE=$(curl -s -X POST "$BASE_URL/docs/upload" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@scripts/test_flow.sh" \
    -F "name=test_flow.sh" \
    -F "mime_type=text/x-shellscript" \
    -F "metadata={\"category\":\"scripts\",\"type\":\"test\"}" \
    -F "is_public=false")
print_api_response "/docs/upload (Private)" "$PRIVATE_DOC_RESPONSE"
PRIVATE_DOC_ID=$(extract_json_value "$PRIVATE_DOC_RESPONSE" "id")
check_api_response "$PRIVATE_DOC_RESPONSE" "Creating private document"

# Create a public document for user1
echo -e "\n${BLUE}Creating public document for user1...${NC}"
PUBLIC_DOC_RESPONSE=$(curl -s -X POST "$BASE_URL/docs/upload" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@scripts/test_flow.sh" \
    -F "name=public_test_flow.sh" \
    -F "mime_type=text/x-shellscript" \
    -F "metadata={\"category\":\"scripts\",\"type\":\"test\",\"visibility\":\"public\"}" \
    -F "is_public=true" \
    -F "unique_name=test_flow_123")
print_api_response "/docs/upload (Public)" "$PUBLIC_DOC_RESPONSE"
PUBLIC_DOC_ID=$(extract_json_value "$PUBLIC_DOC_RESPONSE" "id")
check_api_response "$PUBLIC_DOC_RESPONSE" "Creating public document"

# List documents for user1
echo -e "\n${BLUE}Listing documents for user1...${NC}"
DOCS_RESPONSE=$(curl -s -L -X GET "$BASE_URL/docs?skip=0&limit=10" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/docs (List)" "$DOCS_RESPONSE"

# Get private document content
echo -e "\n${BLUE}Getting private document content...${NC}"
PRIVATE_CONTENT_RESPONSE=$(curl -s -X GET "$BASE_URL/docs/$PRIVATE_DOC_ID/content" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/docs/$PRIVATE_DOC_ID/content (Private)" "$PRIVATE_CONTENT_RESPONSE"

# Get public document content
echo -e "\n${BLUE}Getting public document content...${NC}"
PUBLIC_CONTENT_RESPONSE=$(curl -s -X GET "$BASE_URL/docs/$PUBLIC_DOC_ID/content" \
    -H "Authorization: Bearer $TOKEN2")
print_api_response "/docs/$PUBLIC_DOC_ID/content (Public)" "$PUBLIC_CONTENT_RESPONSE"

# Try to access private document with user2 (should fail)
echo -e "\n${BLUE}Testing private document access with user2...${NC}"
PRIVATE_CONTENT_RESPONSE=$(curl -s -X GET "$BASE_URL/docs/$PRIVATE_DOC_ID/content" \
    -H "Authorization: Bearer $TOKEN2")
print_api_response "/docs/$PRIVATE_DOC_ID/content (Unauthorized)" "$PRIVATE_CONTENT_RESPONSE"

# Update document metadata
echo -e "\n${BLUE}Updating document metadata...${NC}"
UPDATE_DOC_RESPONSE=$(curl -s -X PUT "$BASE_URL/docs/$PRIVATE_DOC_ID" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "updated_test_flow.sh",
        "metadata": {
            "category": "scripts",
            "type": "test",
            "version": "1.1",
            "last_updated": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
        }
    }')
print_api_response "/docs/$PRIVATE_DOC_ID (Update)" "$UPDATE_DOC_RESPONSE"
check_api_response "$UPDATE_DOC_RESPONSE" "Updating document metadata"

# Try to access private document with user2's token (should fail)
echo -e "\n${BLUE}Testing document access control...${NC}"
UNAUTHORIZED_DOC_RESPONSE=$(curl -s -X GET "$BASE_URL/docs/$PRIVATE_DOC_ID/content" \
    -H "Authorization: Bearer $TOKEN2")
print_api_response "/docs/$PRIVATE_DOC_ID/content (Unauthorized)" "$UNAUTHORIZED_DOC_RESPONSE"

# Delete private document
echo -e "\n${BLUE}Deleting private document...${NC}"
DELETE_DOC_RESPONSE=$(curl -s -X DELETE "$BASE_URL/docs/$PRIVATE_DOC_ID" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/docs/$PRIVATE_DOC_ID (Delete)" "$DELETE_DOC_RESPONSE"
check_api_response "$DELETE_DOC_RESPONSE" "Deleting document"

# Verify document deletion
VERIFY_DOC_DELETE_RESPONSE=$(curl -s -X GET "$BASE_URL/docs/$PRIVATE_DOC_ID" \
    -H "Authorization: Bearer $TOKEN1")
print_api_response "/docs/$PRIVATE_DOC_ID (Verify Delete)" "$VERIFY_DOC_DELETE_RESPONSE"

# Clean up at the end
cleanup_storage

echo -e "\n${GREEN}Test flow completed!${NC}"

echo -e "\n${BLUE}Test logs have been saved to $LOG_FILE${NC}"
