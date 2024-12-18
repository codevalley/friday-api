from abc import abstractmethod
from typing import (
    Generic,
    List,
    TypeVar,
    Optional,
    Dict,
    Any,
)

# Type definition for Model
M = TypeVar("M")

# Type definition for Unique Id
K = TypeVar("K")


#################################
# Abstract Class for Repository #
#################################
class RepositoryMeta(Generic[M, K]):
    # Create a new instance of the Model
    @abstractmethod
    def create(self, instance: M) -> M:
        pass

    # Delete an existing instance of the Model
    @abstractmethod
    def delete(self, id: K) -> bool:
        pass

    # Fetch an existing instance of the Model by it's unique Id
    @abstractmethod
    def get(self, id: K) -> Optional[M]:
        pass

    # Lists all existing instance of the Model
    @abstractmethod
    def list(
        self, skip: int = 0, limit: int = 100
    ) -> List[M]:
        pass

    # Updates an existing instance of the Model
    @abstractmethod
    def update(
        self, id: K, data: Dict[str, Any]
    ) -> Optional[M]:
        pass
