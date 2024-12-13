# GraphQL Query Examples

## Activities

### Queries

#### Get Activity by ID

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

#### List Activities

```graphql
query ListActivities {
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

### Mutations

#### Create Activity

```graphql
mutation CreateActivity {
  createActivity(
    activity: {
      name: "New Activity",
      description: "Activity description",
      activitySchema: "{\"type\":\"object\",\"properties\":{\"value\":{\"type\":\"string\"}}}",
      icon: "activity-icon",
      color: "#00FF00"
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

#### Update Activity

```graphql
mutation UpdateActivity {
  updateActivity(
    activityId: 1,
    activity: {
      name: "Updated Activity",
      description: "Updated description",
      activitySchema: "{\"type\":\"object\",\"properties\":{\"value\":{\"type\":\"string\"}}}",
      icon: "new-icon",
      color: "#FF0000"
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

## Moments

### Query

#### Get Moment by ID

```graphql
query GetMoment {
  getMoment(id: 1) {
    id
    timestamp
    data
    activity {
      id
      name
      description
    }
  }
}
```

#### List Moments

```graphql
query ListMoments {
  getMoments(
    page: 1,
    size: 10,
    activityId: 1,
    startTime: "2024-01-01T00:00:00Z",
    endTime: "2024-12-31T23:59:59Z"
  ) {
    items {
      id
      timestamp
      data
      activity {
        id
        name
      }
    }
    total
    page
    size
    pages
  }
}
```

### Mutation

#### Create Moment

```graphql
mutation CreateMoment {
  createMoment(
    moment: {
      activityId: 1,
      data: "{\"value\":\"Sample value\"}",
      timestamp: "2024-12-12T16:30:00Z"
    }
  ) {
    id
    timestamp
    data
    activity {
      id
      name
    }
  }
}
```

#### Update Moment

```graphql
mutation UpdateMoment {
  updateMoment(
    momentId: 1,
    moment: {
      activityId: 1,
      data: "{\"value\":\"Updated value\"}",
      timestamp: "2024-12-12T16:30:00Z"
    }
  ) {
    id
    timestamp
    data
    activity {
      id
      name
    }
  }
}
