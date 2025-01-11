#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Function to print test result
print_result() {
    local step="$1"
    local success="$2"
    local error_msg="$3"

    all_steps+=("$step")
    if [ "$success" = true ]; then
        echo -e "$step [${GREEN}success${NC}]"
    else
        echo -e "$step [${RED}failed${NC}]"
        if [ ! -z "$error_msg" ]; then
            echo -e "${RED}Error: $error_msg${NC}"
        fi
        failed_steps+=("$step: $error_msg")
    fi
    echo
}

# Test flow
echo "Starting test flow..."
echo

# 1. Get auth token for user1
echo "1. Getting auth token for user1..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"key_id": "user1", "user_secret": "secret1"}')

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"data":"[^"]*"' | cut -d'"' -f4)
if [ ! -z "$TOKEN" ]; then
    print_result "1. Getting auth token for user1" true
else
    print_result "1. Getting auth token for user1" false "Failed to get token"
    exit 1
fi

# 2. Create reading activity
echo "2. Creating reading activity..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/activities" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
        "name": "Reading",
        "description": "Track reading sessions",
        "activity_schema": {
            "type": "object",
            "properties": {
                "book": {"type": "string"},
                "pages": {"type": "number"}
            },
            "required": ["book", "pages"]
        },
        "icon": "📚",
        "color": "#4A90E2"
    }')
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "2. Creating reading activity" true
else
    print_result "2. Creating reading activity" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# 3. Get activity schema render
echo "3. Getting activity schema render..."
RESPONSE=$(curl -s "http://localhost:8000/v1/activities/1/schema" \
    -H "Authorization: Bearer $TOKEN")
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "3. Getting activity schema render" true
else
    print_result "3. Getting activity schema render" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# 4. Create first moment
echo "4. Creating first moment..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/moments" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
        "activity_id": 1,
        "data": {
            "book": "Book 1",
            "pages": 50
        },
        "timestamp": "2024-12-12T13:30:00Z"
    }')
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "4. Creating first moment" true
else
    print_result "4. Creating first moment" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# 5. Create second moment
echo "5. Creating second moment..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/moments" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
        "activity_id": 1,
        "data": {
            "book": "Book 2",
            "pages": 100
        },
        "timestamp": "2024-12-12T14:30:00Z"
    }')
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "5. Creating second moment" true
else
    print_result "5. Creating second moment" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# 6. Get auth token for user2
echo "6. Getting auth token for user2..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"key_id": "user2", "user_secret": "secret2"}')
TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"data":"[^"]*"' | cut -d'"' -f4)
if [ ! -z "$TOKEN" ]; then
    print_result "6. Getting auth token for user2" true
else
    print_result "6. Getting auth token for user2" false "Failed to get token"
fi

# 7. Create coding activity for user2
echo "7. Creating coding activity for user2..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/activities" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
        "name": "Coding",
        "description": "Track coding sessions",
        "activity_schema": {
            "type": "object",
            "properties": {
                "language": {"type": "string"},
                "hours": {"type": "number"}
            },
            "required": ["language", "hours"]
        },
        "icon": "💻",
        "color": "#2ECC71"
    }')
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "7. Creating coding activity for user2" true
else
    print_result "7. Creating coding activity for user2" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# 8. List activities for user2
echo "8. Listing activities for user2..."
RESPONSE=$(curl -s "http://localhost:8000/v1/activities" \
    -H "Authorization: Bearer $TOKEN")
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "8. Listing activities for user2" true
else
    print_result "8. Listing activities for user2" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# 9. List moments for user2
echo "9. Listing moments for user2..."
RESPONSE=$(curl -s "http://localhost:8000/v1/moments" \
    -H "Authorization: Bearer $TOKEN")
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "9. Listing moments for user2" true
else
    print_result "9. Listing moments for user2" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# 10. Get specific activity for user1
echo "10. Getting specific activity for user1..."
RESPONSE=$(curl -s "http://localhost:8000/v1/activities/1" \
    -H "Authorization: Bearer $TOKEN")
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "10. Getting specific activity for user1" true
else
    print_result "10. Getting specific activity for user1" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# 11. Get specific moment for user1
echo "11. Getting specific moment for user1..."
RESPONSE=$(curl -s "http://localhost:8000/v1/moments/1" \
    -H "Authorization: Bearer $TOKEN")
ERROR=$(echo $RESPONSE | grep -o '"error":[^}]*}' || echo "")
if [ -z "$ERROR" ] || [ "$ERROR" = '"error":null' ]; then
    print_result "11. Getting specific moment for user1" true
else
    print_result "11. Getting specific moment for user1" false "$(echo $ERROR | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
fi

# Initialize step tracking at the start
declare -a failed_steps=()
declare -a all_steps=()
step_count=11

# Print final summary at the end
echo
echo "Test Summary"
echo "============"
for step in "${all_steps[@]}"; do
    if [[ " ${failed_steps[@]} " =~ " ${step}:" ]]; then
        for failed in "${failed_steps[@]}"; do
            if [[ $failed == ${step}:* ]]; then
                echo -e "${RED}✗ $failed${NC}"
                break
            fi
        done
    else
        echo -e "${GREEN}✓ $step${NC}"
    fi
done

echo
echo -e "Total steps: ${step_count}"
echo -e "Passed: ${GREEN}$((step_count - ${#failed_steps[@]}))${NC}"
if [ ${#failed_steps[@]} -gt 0 ]; then
    echo -e "Failed: ${RED}${#failed_steps[@]}${NC}"
    exit 1
else
    echo -e "\n${GREEN}All steps passed successfully!${NC}"
fi
