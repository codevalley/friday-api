#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

echo -e "${BLUE}Starting test flow...${NC}"

BASE_URL="http://localhost:8000/v1"

# Function to extract value from JSON response
# Usage: extract_json_value "response" "field"
extract_json_value() {
    local response=$1
    local field=$2

    # First try to extract from data field (GenericResponse format)
    # This handles nested fields like data.id, data.items, etc.
    value=$(echo "$response" | grep -o "\"data\":{[^}]*\"$field\":[[:space:]]*[^,}]*" | grep -o "\"$field\":[[:space:]]*[^,}]*" | sed -E "s/\"$field\":[[:space:]]*//;s/\"//g")

    # If not found in data field, try direct field (for backward compatibility)
    if [ -z "$value" ]; then
        value=$(echo "$response" | grep -o "\"$field\":[[:space:]]*[^,}]*" | sed -E "s/\"$field\":[[:space:]]*//;s/\"//g")
    fi

    # Trim any whitespace
    value=$(echo "$value" | sed -E 's/^[[:space:]]*|[[:space:]]*$//g')

    echo "$value"
}

# Function to check API response
check_api_response() {
    local response=$1
    local context=$2

    # Check for error response
    if echo "$response" | grep -q "\"detail\""; then
        echo -e "${RED}✗ Failed - $context${NC}"
        echo "$response"
        exit 1
    fi

    # Check for data field (GenericResponse format)
    if ! echo "$response" | grep -q "\"data\":{"; then
        # Special case for auth endpoints that might not be wrapped yet
        if echo "$response" | grep -q "\"user_secret\":\|\"access_token\":"; then
            echo -e "${GREEN}✓ Success${NC}"
            return
        fi
        echo -e "${RED}✗ Failed - $context - Invalid response format${NC}"
        echo "$response"
        exit 1
    fi

    echo -e "${GREEN}✓ Success${NC}"
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
USER1_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "user1"
    }')
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
ACTIVITY1_ID=$(extract_json_value "$ACTIVITY1_RESPONSE" "id")
echo "Activity1 ID (raw): '$ACTIVITY1_ID'"  # Debug output with quotes
check_api_response "$ACTIVITY1_RESPONSE" "Creating reading activity"

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
ACTIVITY2_ID=$(extract_json_value "$ACTIVITY2_RESPONSE" "id")
echo "Activity2 ID (raw): '$ACTIVITY2_ID'"  # Debug output with quotes
check_api_response "$ACTIVITY2_RESPONSE" "Creating exercise activity"

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

echo -e "\n${GREEN}Test flow completed!${NC}"
