"""Value objects for the domain models."""

import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, Set
from domain.exceptions import ActivityValidationError


@dataclass(frozen=True)
class Color:
    """Value object representing a color in hex format.

    The color must be in #RRGGBB format, where RR, GG, and BB are
    hexadecimal values between 00 and FF.
    """

    value: str

    def __post_init__(self):
        """Validate the color format after initialization."""
        if not self.value:
            raise ActivityValidationError.invalid_color(
                "empty"
            )

        if not re.match(r"^#[0-9A-Fa-f]{6}$", self.value):
            raise ActivityValidationError.invalid_color(
                self.value
            )

    @classmethod
    def from_string(
        cls, value: Optional[str]
    ) -> Optional["Color"]:
        """Create a Color from a string value.

        Args:
            value: Color string in #RRGGBB format

        Returns:
            Color instance or None if value is None

        Raises:
            ActivityValidationError: If color format is invalid
        """
        if value is None:
            return None
        return cls(value)

    def __str__(self) -> str:
        """Return the string representation of the color."""
        return self.value


@dataclass(frozen=True)
class ActivitySchema:
    """Value object representing a JSON schema for activity data.

    The schema must be a valid JSON Schema object with specific
    constraints for activity data validation.

    Attributes:
        value: The raw schema dictionary
        properties: Dictionary of property definitions
        pattern_properties: Dictionary of pattern property definitions
        required_fields: Set of required field names
        additional_properties: Whether additional properties are allowed
        min_properties: Minimum number of properties required
        max_properties: Maximum number of properties allowed
    """

    value: Dict[str, Any]
    properties: Dict[str, Any] = None
    pattern_properties: Dict[str, Any] = None
    required_fields: Set[str] = None
    additional_properties: bool = None
    min_properties: Optional[int] = None
    max_properties: Optional[int] = None

    def __post_init__(self):
        """Validate the schema after initialization."""
        # Initialize derived fields from value
        object.__setattr__(
            self,
            "properties",
            self.value.get("properties", {}),
        )
        object.__setattr__(
            self,
            "pattern_properties",
            self.value.get("patternProperties", {}),
        )
        object.__setattr__(
            self,
            "required_fields",
            set(self.value.get("required", [])),
        )
        object.__setattr__(
            self,
            "additional_properties",
            self.value.get("additionalProperties", True),
        )
        object.__setattr__(
            self,
            "min_properties",
            self.value.get("minProperties"),
        )
        object.__setattr__(
            self,
            "max_properties",
            self.value.get("maxProperties"),
        )
        self._validate()

    def _validate(self) -> None:
        """Validate the schema structure.

        Raises:
            ActivityValidationError: If schema is invalid
        """
        if not isinstance(self.value, dict):
            raise ActivityValidationError.invalid_field_value(
                "activity_schema",
                "Activity schema must be a dictionary",
            )

        if "type" not in self.value:
            raise ActivityValidationError.missing_type_field()

        if self.value["type"] != "object":
            raise ActivityValidationError.invalid_schema_type()

        # Validate properties if present
        if self.properties:
            if not isinstance(self.properties, dict):
                raise ActivityValidationError.invalid_field_value(
                    "properties",
                    "Schema properties must be a dictionary",
                )

            for (
                prop_name,
                prop_schema,
            ) in self.properties.items():
                if not isinstance(prop_schema, dict):
                    raise ActivityValidationError.invalid_field_value(
                        prop_name,
                        f"Property {prop_name} schema must be a dictionary",
                    )
                if (
                    "$ref" not in prop_schema
                    and "type" not in prop_schema
                ):
                    raise ActivityValidationError.invalid_field_value(
                        prop_name,
                        f"Property {prop_name} must specify a type",
                    )

        # Validate pattern properties if present
        if self.pattern_properties:
            if not isinstance(
                self.pattern_properties, dict
            ):
                raise ActivityValidationError.invalid_field_value(
                    "patternProperties",
                    "Pattern properties must be a dictionary",
                )

            for (
                pattern,
                prop_schema,
            ) in self.pattern_properties.items():
                if not isinstance(prop_schema, dict):
                    raise ActivityValidationError.invalid_field_value(
                        pattern,
                        f"Pattern {pattern} schema must be a dictionary",
                    )
                if (
                    "$ref" not in prop_schema
                    and "type" not in prop_schema
                ):
                    raise ActivityValidationError.invalid_field_value(
                        pattern,
                        f"Pattern {pattern} must specify a type",
                    )

        # Check for schema constraints
        has_constraints = bool(
            self.required_fields
            or not self.additional_properties
            or self.min_properties is not None
            or self.max_properties is not None
        )
        has_properties = bool(self.properties)
        has_pattern_props = bool(self.pattern_properties)

        if has_constraints and not (
            has_properties or has_pattern_props
        ):
            raise ActivityValidationError.invalid_schema_constraints()

    @classmethod
    def from_dict(
        cls, value: Dict[str, Any]
    ) -> "ActivitySchema":
        """Create an ActivitySchema from a dictionary.

        Args:
            value: Schema dictionary

        Returns:
            ActivitySchema instance

        Raises:
            ActivityValidationError: If schema is invalid
        """
        return cls(value=value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary.

        Returns:
            Dictionary representation of the schema
        """
        return self.value

    def __str__(self) -> str:
        """Return a string representation of the schema."""
        return str(self.value)
