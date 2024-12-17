#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

echo -e "${BLUE}Starting GraphQL test flow...${NC}"

BASE_URL="http://localhost:8000"

# Function to extract value from JSON response
extract_json_value() {
    local response=$1
    local field=$2

    # Try using jq if available
    if command -v jq &> /dev/null; then
        echo "$response" | jq -r ".$field"
        return
    fi

    # Fallback: basic string manipulation
    # Handle both string and number values
    value=$(echo "$response" | grep -o "\"$field\":[[:space:]]*[\"0-9][^,}]*" | sed -E "s/\"$field\":[[:space:]]*//;s/\"//g")
    echo "$value"
}

# Function to check API response
check_api_response() {
    local response=$1
    local context=$2

    # Check for error response
    if echo "$response" | grep -q "\"errors\""; then
        echo -e "${RED}✗ Failed - $context${NC}"
        echo "$response"
        exit 1
    fi

    echo -e "${GREEN}✓ Success${NC}"
}

# Function to extract GraphQL data
extract_graphql_value() {
    local response=$1
    local field=$2

    # Try using jq if available
    if command -v jq &> /dev/null; then
        echo "$response" | jq -r ".data.$field.id"
        return
    fi

    # Fallback: basic string manipulation for GraphQL response
    value=$(echo "$response" | grep -o "\"id\":[[:space:]]*[0-9][^,}]*" | head -n1 | sed -E "s/\"id\":[[:space:]]*//")
    echo "$value"
}

# Store GraphQL queries
READING_SCHEMA="{\\\"type\\\":\\\"object\\\",\\\"properties\\\":{\\\"book\\\":{\\\"type\\\":\\\"string\\\"},\\\"pages\\\":{\\\"type\\\":\\\"number\\\"}},\\\"required\\\":[\\\"book\\\",\\\"pages\\\"]}"

EXERCISE_SCHEMA="{\\\"type\\\":\\\"object\\\",\\\"properties\\\":{\\\"type\\\":{\\\"type\\\":\\\"string\\\"},\\\"duration\\\":{\\\"type\\\":\\\"number\\\"}},\\\"required\\\":[\\\"type\\\",\\\"duration\\\"]}"

CODING_SCHEMA="{\\\"type\\\":\\\"object\\\",\\\"properties\\\":{\\\"language\\\":{\\\"type\\\":\\\"string\\\"},\\\"hours\\\":{\\\"type\\\":\\\"number\\\"}},\\\"required\\\":[\\\"language\\\",\\\"hours\\\"]}"

# 1. Create first user (using REST API for registration)
echo -e "\n${BLUE}1. Creating first user (guser1)...${NC}"
USER1_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "guser1"
    }')
USER1_API_KEY=$(extract_json_value "$USER1_RESPONSE" "user_secret")
echo "GUser1 Response: $USER1_RESPONSE"
echo "GUser1 API Key: $USER1_API_KEY"
check_api_response "$USER1_RESPONSE" "User registration"

# Get token for guser1 (using REST API for token)
echo -e "\n${BLUE}Getting token for guser1...${NC}"
TOKEN1_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/auth/token" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_secret\": \"$USER1_API_KEY\"
    }")
TOKEN1=$(extract_json_value "$TOKEN1_RESPONSE" "access_token")
echo "Token Response: $TOKEN1_RESPONSE"
echo "Token: $TOKEN1"
check_api_response "$TOKEN1_RESPONSE" "Token generation"

# 2. Create activities for guser1 using GraphQL
echo -e "\n${BLUE}2. Creating activities for guser1...${NC}"
# Activity 1: Reading
ACTIVITY1_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d "{
        \"query\": \"mutation { createActivity(activity: { name: \\\"Reading\\\", description: \\\"Track reading sessions\\\", activitySchema: \\\"${READING_SCHEMA}\\\", icon: \\\"📚\\\", color: \\\"#4A90E2\\\" }) { id name description activitySchema icon color } }\"
    }")
ACTIVITY1_ID=$(extract_graphql_value "$ACTIVITY1_RESPONSE" "createActivity")
echo "Activity1 Response: $ACTIVITY1_RESPONSE"
echo "Activity1 ID: $ACTIVITY1_ID"
check_api_response "$ACTIVITY1_RESPONSE" "Creating reading activity"

# Activity 2: Exercise
ACTIVITY2_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d "{
        \"query\": \"mutation { createActivity(activity: { name: \\\"Exercise\\\", description: \\\"Track workouts\\\", activitySchema: \\\"${EXERCISE_SCHEMA}\\\", icon: \\\"💪\\\", color: \\\"#FF5733\\\" }) { id name description activitySchema icon color } }\"
    }")
ACTIVITY2_ID=$(extract_graphql_value "$ACTIVITY2_RESPONSE" "createActivity")
echo "Activity2 Response: $ACTIVITY2_RESPONSE"
echo "Activity2 ID: $ACTIVITY2_ID"
check_api_response "$ACTIVITY2_RESPONSE" "Creating exercise activity"

# 3. Create moments for guser1
echo -e "\n${BLUE}3. Creating moments for guser1...${NC}"
# Reading moments
for i in {1..2}; do
    echo "Creating reading moment $i with activity ID: $ACTIVITY1_ID"
    MOMENT_DATA="{\\\"book\\\":\\\"Book $i\\\",\\\"pages\\\":$((i * 50))}"
    MOMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
        -H "Authorization: Bearer $TOKEN1" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"mutation { createMoment(moment: { activityId: $ACTIVITY1_ID, data: \\\"${MOMENT_DATA}\\\", timestamp: \\\"2024-12-12T$((12 + i)):30:00Z\\\" }) { id timestamp data activity { id name } } }\"
        }")
    echo "Reading Moment $i Response: $MOMENT_RESPONSE"
    check_api_response "$MOMENT_RESPONSE" "Creating reading moment $i"
done

# Exercise moments
for i in {1..2}; do
    echo "Creating exercise moment $i with activity ID: $ACTIVITY2_ID"
    MOMENT_DATA="{\\\"type\\\":\\\"Running\\\",\\\"duration\\\":$((i * 30))}"
    MOMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
        -H "Authorization: Bearer $TOKEN1" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"mutation { createMoment(moment: { activityId: $ACTIVITY2_ID, data: \\\"${MOMENT_DATA}\\\", timestamp: \\\"2024-12-12T$((14 + i)):30:00Z\\\" }) { id timestamp data activity { id name } } }\"
        }")
    echo "Exercise Moment $i Response: $MOMENT_RESPONSE"
    check_api_response "$MOMENT_RESPONSE" "Creating exercise moment $i"
done

# 4. Create second user (using REST API for registration)
echo -e "\n${BLUE}4. Creating second user (guser2)...${NC}"
USER2_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "guser2"
    }')
USER2_API_KEY=$(extract_json_value "$USER2_RESPONSE" "user_secret")
echo "GUser2 Response: $USER2_RESPONSE"
echo "GUser2 API Key: $USER2_API_KEY"
check_api_response "$USER2_RESPONSE" "User2 registration"

# Get token for user2 (using REST API for token)
echo -e "\n${BLUE}Getting token for guser2...${NC}"
TOKEN2_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/auth/token" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_secret\": \"$USER2_API_KEY\"
    }")
TOKEN2=$(extract_json_value "$TOKEN2_RESPONSE" "access_token")
echo "Token2 Response: $TOKEN2_RESPONSE"
echo "Token2: $TOKEN2"
check_api_response "$TOKEN2_RESPONSE" "Token2 generation"

# 5. Create activity for user2 using GraphQL
echo -e "\n${BLUE}5. Creating activity for guser2...${NC}"
ACTIVITY3_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Authorization: Bearer $TOKEN2" \
    -H "Content-Type: application/json" \
    -d "{
        \"query\": \"mutation { createActivity(activity: { name: \\\"Coding\\\", description: \\\"Track coding sessions\\\", activitySchema: \\\"${CODING_SCHEMA}\\\", icon: \\\"💻\\\", color: \\\"#2ECC71\\\" }) { id name description activitySchema icon color } }\"
    }")
ACTIVITY3_ID=$(extract_graphql_value "$ACTIVITY3_RESPONSE" "createActivity")
echo "Activity3 Response: $ACTIVITY3_RESPONSE"
echo "Activity3 ID: $ACTIVITY3_ID"
check_api_response "$ACTIVITY3_RESPONSE" "Creating coding activity"

# 6. Create moments for user2
echo -e "\n${BLUE}6. Creating moments for guser2...${NC}"
for i in {1..3}; do
    echo "Creating coding moment $i with activity ID: $ACTIVITY3_ID"
    MOMENT_DATA="{\\\"language\\\":\\\"Python\\\",\\\"hours\\\":$i}"
    MOMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
        -H "Authorization: Bearer $TOKEN2" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"mutation { createMoment(moment: { activityId: $ACTIVITY3_ID, data: \\\"${MOMENT_DATA}\\\", timestamp: \\\"2024-12-12T$((16 + i)):30:00Z\\\" }) { id timestamp data activity { id name } } }\"
        }")
    echo "Coding Moment $i Response: $MOMENT_RESPONSE"
    check_api_response "$MOMENT_RESPONSE" "Creating coding moment $i"
done

# 7. List activities for user2
echo -e "\n${BLUE}7. Listing activities for guser2...${NC}"
ACTIVITIES_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Authorization: Bearer $TOKEN2" \
    -H "Content-Type: application/json" \
    -d "{
        \"query\": \"query { getActivities(skip: 0, limit: 100) { id name description activitySchema icon color momentCount } }\"
    }")
echo "Activities Response: $ACTIVITIES_RESPONSE"
check_api_response "$ACTIVITIES_RESPONSE" "Listing activities"

# 8. List moments for user2
echo -e "\n${BLUE}8. Listing moments for guser2...${NC}"
MOMENTS_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Authorization: Bearer $TOKEN2" \
    -H "Content-Type: application/json" \
    -d "{
        \"query\": \"query { getMoments(page: 1, size: 50) { items { id timestamp data activity { id name } } total page size pages } }\"
    }")
echo "Moments Response: $MOMENTS_RESPONSE"
check_api_response "$MOMENTS_RESPONSE" "Listing moments"

# 9. Get specific activity for user1
echo -e "\n${BLUE}9. Getting specific activity for guser1...${NC}"
ACTIVITY_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d "{
        \"query\": \"query { getActivity(id: $ACTIVITY1_ID) { id name description activitySchema icon color momentCount } }\"
    }")
echo "Activity Response: $ACTIVITY_RESPONSE"
check_api_response "$ACTIVITY_RESPONSE" "Getting specific activity"

# 10. Get specific moment for user1
echo -e "\n${BLUE}10. Getting specific moment for guser1...${NC}"
MOMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d "{
        \"query\": \"query { getMoment(id: 1) { id timestamp data activity { id name } } }\"
    }")
echo "Moment Response: $MOMENT_RESPONSE"
check_api_response "$MOMENT_RESPONSE" "Getting specific moment"

echo -e "\n${GREEN}GraphQL test flow completed!${NC}"
