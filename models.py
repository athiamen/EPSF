from pydantic import BaseModel
from typing import List, Optional

# Define the data model
class Node(BaseModel):
    id: str
    label: str
    type: str  # cause | collision | consequence
    frequency: Optional[float] = None
    severity: Optional[float] = None
    barriers: Optional[List[str]] = []

class Link(BaseModel):
    source: str
    target: str
    