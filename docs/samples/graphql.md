# GraphQL Query Examples

## Moments

### Get a Single Moment by ID
```graphql
query GetMoment {
  getMoment(id: 1) {
    id
    data
    timestamp
    activityId
    activity {
      id
      name
      description
    }
  }
}
```

### List Moments with Filtering and Pagination
```graphql
query GetMoments {
  getMoments(
    page: 1
    size: 10
    activityId: 1
    startTime: "2024-01-01T00:00:00Z"
    endTime: "2024-12-31T23:59:59Z"
  ) {
    items {
      id
      data
      timestamp
      activityId
      activity {
        id
        name
        description
      }
    }
    total
    page
    size
    pages
  }
}
```

### Create a New Moment
```graphql
mutation CreateMoment {
  createMoment(
    moment: {
      activityId: 1
      data: "{\"key\": \"value\"}"
      timestamp: "2024-01-01T12:00:00Z"
    }
  ) {
    id
    data
    timestamp
    activityId
    activity {
      id
      name
    }
  }
}
```

## Activities

### Get a Single Activity
```graphql
query GetActivity {
  getActivity(id: 1) {
    id
    name
    description
    activitySchema
    icon
    color
    moments {
      id
      data
      timestamp
    }
    momentCount
  }
}
```

### List All Activities
```graphql
query GetActivities {
  getActivities(skip: 0, limit: 10) {
    id
    name
    description
    activitySchema
    icon
    color
    momentCount
  }
}
```

### Create a New Activity
```graphql
mutation CreateActivity {
  createActivity(
    activity: {
      name: "Daily Journal"
      description: "Track your daily thoughts and experiences"
      activitySchema: "{\"type\": \"object\", \"properties\": {\"entry\": {\"type\": \"string\"}}}"
      icon: "📝"
      color: "#4A90E2"
    }
  ) {
    id
    name
    description
    activitySchema
    icon
    color
  }
}
```

### Update an Activity
```graphql
mutation UpdateActivity {
  updateActivity(
    activityId: 1
    activity: {
      name: "Updated Journal"
      description: "Updated description"
    }
  ) {
    id
    name
    description
    activitySchema
    icon
    color
  }
}
```
