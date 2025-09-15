# pip install fastapi uvicorn // Pour installer les packages
# uvicorn main:app --reload // Pour lancer le serveur
# http://localhost:8000/docs // Pour voir la doc


from fastapi import FastAPI
from routers import graph, stats, simulation

app = FastAPI()

app.include_router(graph.router, prefix="/graph", tags=["Graph"]) # prefix pour ajouter un préfixe à l'URL
app.include_router(stats.router, prefix="/stats", tags=["Stats"]) # tags pour regrouper les routes dans la doc
app.include_router(simulation.router, prefix="/simulate", tags=["Simulation"]) # tags pour regrouper les routes dans la doc



predicats = [
    "rdfs:label",
    "rdfs:comment",
    "rdfs:domain",
    "rdfs:range",
    "owl:equivalentProperty",
    "iss:occurrenceTownOrCity",
]

prefixes = {
    "":     "https://securite-ferroviaire.fr/ontology/",   # (optionnel) préfixe vide
    "iss":  "http://data.europa.eu/949/iss/",
    # ajouter vos autres préfixes si besoin…
}

data = extract_from_ttl(
    ttl_path="mon_fichier.ttl",
    predicates=predicats,
    prefixes=prefixes,
    to_excel_path="extraction_predicats.xlsx"  # retirez si vous ne voulez pas d’Excel
)

# Accès en mémoire
# print(data[":GeoLocation"]["rdfs:label"])