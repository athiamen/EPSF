# pip install fastapi uvicorn // Pour installer les packages
# uvicorn main:app --reload // Pour lancer le serveur
# http://localhost:8000/docs // Pour voir la doc


from fastapi import FastAPI
from routers import graph, stats, simulation

app = FastAPI()

app.include_router(graph.router, prefix="/graph", tags=["Graph"]) # prefix pour ajouter un préfixe à l'URL
app.include_router(stats.router, prefix="/stats", tags=["Stats"]) # tags pour regrouper les routes dans la doc
app.include_router(simulation.router, prefix="/simulate", tags=["Simulation"]) # tags pour regrouper les routes dans la doc
