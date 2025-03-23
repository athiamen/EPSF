from fastapi import APIRouter
from data.np_collision_data import nodes, links

router = APIRouter()

@router.get("/nodes")
def get_nodes(): # Retourne les noeuds
    return nodes

@router.get("/links")
def get_links():# Retourne les liens
    return links

@router.get("/node/{node_id}")
def get_node(node_id: str): # Retourne un noeud par son id
    for node in nodes:
        if node.id == node_id:
            return node
