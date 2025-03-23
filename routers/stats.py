from fastapi import APIRouter
from data.np_collision_data import nodes
from collections import Counter

router = APIRouter()

@router.get("/frequencies")
def get_frequencies(): # Retourne les fréquences des noeuds
    return {n.id: n.frequency for n in nodes if n.frequency}

@router.get("/severities")
def get_severities(): # Retourne les severités des noeuds
    return {n.id: n.severity for n in nodes if n.severity}

@router.get("/by-type")
def stats_by_type(): # Compte le nombre de noeuds par type
    counter = Counter([n.type for n in nodes])
    return dict(counter)
