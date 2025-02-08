#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'
YELLOW='\033[0;33m'

# Create a log file
LOG_FILE="test_note_extraction.log"
echo "Starting test flow at $(date)" > $LOG_FILE

# parse optional argument for the API base URL
BASE_URL="${1:-"http://localhost:8000/v1"}"
echo "Using base URL: $BASE_URL" >> $LOG_FILE

# Function to extract value from JSON response
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

# Function to wait for note processing
wait_for_note_processing() {
    local note_id=$1
    local token=$2
    local max_attempts=10
    local attempt=1
    local status=""

    echo -e "\n${BLUE}Waiting for note $note_id to be processed...${NC}"

    while [ $attempt -le $max_attempts ]; do
        local response=$(curl -s -X GET "$BASE_URL/notes/$note_id" \
            -H "Authorization: Bearer $token")
        status=$(extract_json_value "$response" "processing_status")

        case "$status" in
            "COMPLETED")
                echo -e "${GREEN}Note processing completed successfully${NC}"
                return 0
                ;;
            "FAILED")
                echo -e "${RED}Note processing failed${NC}"
                return 1
                ;;
            *)
                echo "Processing status: $status (attempt $attempt/$max_attempts)"
                ;;
        esac

        sleep 1
        attempt=$((attempt + 1))
    done

    echo -e "${RED}Note processing timed out after $max_attempts attempts${NC}"
    return 1
}

# Initialize database
echo -e "\n${BLUE}Initializing database...${NC}"

# Use test database configuration
export DATABASE_NAME=test_fridaystore
export DATABASE_USERNAME=root
export DATABASE_PASSWORD=1234567890

# Initialize the database
mysql -u"$DATABASE_USERNAME" -p"$DATABASE_PASSWORD" < scripts/init_database.sql 2>&1 | tee -a "$LOG_FILE"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "Failed to initialize database" | tee -a "$LOG_FILE"
    exit 1
fi
echo -e "${GREEN}Database initialized successfully${NC}"

echo -e "${BLUE}1. Creating test user...${NC}"
USER1_RESPONSE=$(curl -s -S -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "test_user"
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

echo -e "\n${BLUE}2. Creating test notes with dates...${NC}"

# Test cases with different date formats
declare -a test_notes=(
    "Need to finish report by this Saturday"
    "Team meeting scheduled for next Tuesday at 2pm"
    "Project deadline is tomorrow morning"
    "Review code changes by end of next week"
    "Submit documentation by this Friday 5pm"
)

for note_content in "${test_notes[@]}"; do
    echo -e "\n${BLUE}Creating note: $note_content${NC}"
    NOTE_RESPONSE=$(curl -s -X POST "$BASE_URL/notes" \
        -H "Authorization: Bearer $TOKEN1" \
        -H "Content-Type: application/json" \
        -d "{
            \"content\": \"$note_content\"
        }")

    NOTE_ID=$(extract_json_value "$NOTE_RESPONSE" "id")
    echo "Note Response: $NOTE_RESPONSE"
    echo "Note ID: $NOTE_ID"
    check_api_response "$NOTE_RESPONSE" "Creating note"

    echo -e "\n${BLUE}Waiting for note $NOTE_ID to be processed...${NC}"
    wait_for_note_processing "$NOTE_ID" "$TOKEN1"

    echo -e "\n${BLUE}Getting processed note and extracted tasks...${NC}"
    PROCESSED_NOTE=$(curl -s -X GET "$BASE_URL/notes/$NOTE_ID" \
        -H "Authorization: Bearer $TOKEN1")

    echo -e "\nProcessed Note Response:"
    echo "$PROCESSED_NOTE" | python3 -m json.tool

    # Get tasks created from this note
    TASKS_RESPONSE=$(curl -s -X GET "$BASE_URL/tasks?source_note_id=$NOTE_ID" \
        -H "Authorization: Bearer $TOKEN1")

    echo -e "\nExtracted Tasks:"
    if check_api_response "$TASKS_RESPONSE" "Getting tasks"; then
        echo "$TASKS_RESPONSE" | python3 -m json.tool
    else
        echo -e "${RED}Failed to get tasks${NC}"
    fi

    sleep 2  # Brief pause between notes
done

echo -e "\n${GREEN}Test completed!${NC}"
echo -e "\n${BLUE}Test logs have been saved to $LOG_FILE${NC}"
