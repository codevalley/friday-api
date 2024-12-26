from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class RoboConfig:
    """Configuration for Robo service."""

    api_key: str
    model_name: str
    max_retries: int = 3
    timeout_seconds: int = 30
    temperature: float = 0.7


@dataclass
class RoboProcessingResult:
    """Result of a Robo processing operation."""

    content: str
    metadata: Dict[str, Any]
    tokens_used: int
    model_name: str
    created_at: datetime = datetime.utcnow()


class RoboService(ABC):
    """Interface for Robo service operations."""

    @abstractmethod
    async def process_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process text input and return enhanced/analyzed result."""
        pass

    @abstractmethod
    async def extract_entities(
        self, text: str, entity_types: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract specified entity types from text."""
        pass

    @abstractmethod
    async def validate_content(
        self, content: str, validation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate content against specified rules."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is operational."""
        pass
