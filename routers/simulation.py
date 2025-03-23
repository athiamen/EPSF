from fastapi import APIRouter, Query
from data.np_collision_data import nodes

router = APIRouter()

@router.get("/impacted-nodes")
def simulate_missing_barriers(missing: list[str] = Query(...)): # Retourne les noeuds impactés par les barrières manquantes
    impacted = []
    for node in nodes:
        if node.barriers:
            if any(bar in node.barriers for bar in missing):
                impacted.append(node)
    return impacted
