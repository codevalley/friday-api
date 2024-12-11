# Domain Models

## Overview

Friday's domain model is built around the concept of life events - discrete moments or activities in a person's life that they want to record and analyze. The model is designed to be flexible and extensible, allowing for various types of life events to be recorded with their specific data structures.

## Core Entities

### Moment

The `Moment` entity represents a single moment or event in a person's life. It is the core domain entity of our life logging system.

```python
class MomentModel(Base):
    __tablename__ = "moments"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)  # Stored in UTC
    activity_id = Column(Integer, ForeignKey("activities.id"))
    data = Column(JSON)  # Flexible schema based on activity type
    
    # Relationships
    activity = relationship("ActivityModel", back_populates="moments")
```

#### Key Attributes:
- `id`: Unique identifier for the moment
- `timestamp`: UTC timestamp when the moment occurred
- `activity_id`: Reference to the type of activity this moment represents
- `data`: JSON data specific to the activity type, validated against the activity's schema

### Activity

The `Activity` entity defines different types of activities that can be logged as moments.

```python
class ActivityModel(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    activity_schema = Column(JSON)  # JSON Schema for validating moment data
    icon = Column(String)  # Icon identifier or URL
    color = Column(String)  # Color code for UI representation
    
    # Relationships
    moments = relationship("MomentModel", back_populates="activity")
```

#### Key Attributes:
- `id`: Unique identifier for the activity type
- `name`: Unique name of the activity
- `description`: Detailed description of what this activity represents
- `activity_schema`: JSON Schema defining the structure of moment data for this activity
- `icon`: Visual representation identifier
- `color`: Color code for UI consistency

## Value Objects

### ActivitySchema
The activity schema is a JSON Schema definition that specifies the structure and validation rules for moment data. Example:

```json
{
    "type": "object",
    "properties": {
        "location": {
            "type": "object",
            "properties": {
                "latitude": { "type": "number" },
                "longitude": { "type": "number" }
            }
        },
        "notes": { "type": "string" },
        "mood": {
            "type": "string",
            "enum": ["happy", "neutral", "sad"]
        }
    }
}
```

## Design Decisions

1. **Flexible Data Storage**
   - Using JSON for moment data allows for:
     - Different data structures per activity type
     - Easy addition of new activity types
     - Schema evolution without database migrations
     - Rich data storage with nested structures

2. **Schema Validation**
   - JSON Schema in Activity ensures:
     - Data consistency
     - Type safety
     - Required field validation
     - Enumerated values where appropriate

3. **Performance Considerations**
   - Indexed fields:
     - `timestamp` for temporal queries
     - `activity_id` for filtering
     - `id` for lookups
   - Timezone support in timestamps

4. **Relationships**
   - One-to-many between Activity and Moment
   - Cascade deletion of moments when activity is deleted
   - Bidirectional relationships for efficient querying

## Built-in Activity Types

Friday comes with several pre-defined activity types:

1. **Photo Moments**
   - Capture moments with images
   - Support for location and captions
   - Optional tagging

2. **Meal Moments**
   - Track food consumption
   - Categorize by meal type
   - Record individual food items and calories

3. **Exercise Moments**
   - Log physical activities
   - Track duration and intensity
   - Support for various exercise types

4. **Note Moments**
   - Quick text notes or thoughts
   - Support for tags and mood
   - Minimal structure for flexibility

5. **Sleep Moments**
   - Track sleep patterns
   - Record quality and interruptions
   - Support for sleep cycle analysis

## Usage Examples

```python
# Creating a new meal moment
meal_moment = MomentModel(
    activity_id=2,  # meal type
    data={
        "meal_type": "lunch",
        "foods": [
            {"name": "Salad", "quantity": "1 bowl", "calories": 200},
            {"name": "Grilled Chicken", "quantity": "200g", "calories": 330}
        ],
        "location": "Home",
        "mood": "satisfied"
    }
)

# Creating a new exercise moment
exercise_moment = MomentModel(
    activity_id=3,  # exercise type
    data={
        "type": "running",
        "duration": 1800,  # in seconds
        "distance": 5.2,   # in kilometers
        "heart_rate": {
            "avg": 145,
            "max": 165
        }
    }
)
```