#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Dict, Any, List, Tuple, Union
import argparse

from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal

try:
    import pandas as pd
except Exception:
    pd = None  # l'export Excel sera désactivé si pandas n'est pas installé


# --- NAMESPACES --------------------------------------------------------------

ISS  = Namespace("http://data.europa.eu/949/iss/")
EPSF = Namespace("https://securite-ferroviaire.fr/ontology/")  # adapte si besoin


# --- OUTILS -----------------------------------------------------------------

def to_py(obj: Union[Literal, URIRef]) -> str:
    """Convertit un objet RDF en string lisible."""
    if isinstance(obj, Literal):
        # conserve la valeur littérale (avec langue/type ignorés ici)
        return str(obj)
    return str(obj)  # URIRef -> IRI en texte


def ensure_list(d: Dict[str, Any], key: str):
    if key not in d or not isinstance(d[key], list):
        d[key] = []


# --- EXTRACTION --------------------------------------------------------------

def extract_from_graph(g: Graph) -> Dict[str, Dict[str, Any]]:
    """
    Extrait pour chaque sujet les champs demandés.
    Renvoie: {sujet_str: { label, comment, domain, range, type, iss, cyrus_equivalent_field, equivalent_property }}
    """
    data: Dict[str, Dict[str, Any]] = {}

    # Liste des prédicats "cœurs"
    predicates = [
        RDFS.label,
        RDFS.comment,
        RDFS.domain,
        RDFS.range,
        OWL.equivalentProperty,    # utile pour équivalences
        OWL.equivalentClass,       # au cas où
        RDF.type,                  # type de la ressource
        EPSF.cyrusEquivalentField, # d'après ton pseudo-code
        # On captera aussi tous prédicats dans l'espace de noms ISS (voir plus bas)
    ]

    # 1) Parcours des prédicats explicites
    for pred in predicates:
        for s, o in g.subject_objects(predicate=pred):
            s_key = str(s)
            obj = to_py(o)
            row = data.setdefault(s_key, {})

            if pred == RDFS.label:
                row["label"] = obj
                # print(f"label : {row['label']}")
            elif pred == RDFS.comment:
                row["comment"] = obj
                # print(f"comment : {row['comment']}")
            elif pred == RDFS.domain:
                ensure_list(row, "domain")
                row["domain"].append(obj)
                # print(f"domaine : {row['domain']}")
            elif pred == RDFS.range:
                ensure_list(row, "range")
                row["range"].append(obj)
                # print(f"valeurs possibles (range) : {row['range']}")
            elif pred == RDF.type:
                ensure_list(row, "type")
                row["type"].append(obj)
                # print(f"type : {row['type']}")
            elif pred == OWL.equivalentProperty:
                ensure_list(row, "equivalent_property")
                row["equivalent_property"].append(obj)
            elif pred == OWL.equivalentClass:
                ensure_list(row, "equivalent_class")
                row["equivalent_class"].append(obj)
            elif pred == EPSF.cyrusEquivalentField:
                # champ spécifique EPSF
                ensure_list(row, "cyrus_equivalent_field")
                row["cyrus_equivalent_field"].append(obj)

    # 2) Capture générique de tout prédicat ISS:* (équivalents/alias éventuels)
    #    On parcourt tous les triplets et on filtre ceux dont le prédicat commence par l’IRI ISS
    for s, p, o in g:
        if isinstance(p, URIRef) and str(p).startswith(str(ISS)):
            s_key = str(s)
            obj = to_py(o)
            row = data.setdefault(s_key, {})
            ensure_list(row, "iss")
            row["iss"].append({"predicate": str(p), "object": obj})
            # print(f"équivalent ISS : {p} -> {obj}")

    return data


# --- EXPORTS ----------------------------------------------------------------

def flatten_for_table(data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aplati le dictionnaire pour en faire une table (liste de lignes) exploitable.
    Les listes sont jointes par ' | ' pour rester lisibles.
    """
    rows: List[Dict[str, Any]] = []
    for subject, fields in data.items():
        row: Dict[str, Any] = {"subject": subject}
        row["label"]  = fields.get("label")
        row["comment"] = fields.get("comment")
        row["domain"] = " | ".join(fields.get("domain", [])) if isinstance(fields.get("domain"), list) else fields.get("domain")
        row["range"]  = " | ".join(fields.get("range", [])) if isinstance(fields.get("range"), list) else fields.get("range")
        row["type"]   = " | ".join(fields.get("type", [])) if isinstance(fields.get("type"), list) else fields.get("type")
        row["equivalent_property"] = " | ".join(fields.get("equivalent_property", [])) if isinstance(fields.get("equivalent_property"), list) else fields.get("equivalent_property")
        row["equivalent_class"]    = " | ".join(fields.get("equivalent_class", [])) if isinstance(fields.get("equivalent_class"), list) else fields.get("equivalent_class")
        row["cyrus_equivalent_field"] = " | ".join(fields.get("cyrus_equivalent_field", [])) if isinstance(fields.get("cyrus_equivalent_field"), list) else fields.get("cyrus_equivalent_field")

        # Pour ISS on concatène predicate=...,object=... entre ' || '
        iss_entries = fields.get("iss", [])
        if iss_entries:
            row["iss"] = " || ".join(f"{e['predicate']} = {e['object']}" for e in iss_entries)
        else:
            row["iss"] = None

        rows.append(row)
    return rows


# --- MAIN -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extraction de champs (label, comment, domain, range, etc.) depuis un fichier TTL.")
    parser.add_argument("ttl", type=Path, help="Chemin du fichier .ttl")
    parser.add_argument("-o", "--output", type=Path, help="Fichier de sortie (xlsx si pandas installé, sinon csv).")
    args = parser.parse_args()

    if not args.ttl.exists():
        raise SystemExit(f"Fichier introuvable: {args.ttl}")

    g = Graph()
    g.parse(args.ttl, format="turtle")

    data = extract_from_graph(g)
    rows = flatten_for_table(data)

    if args.output:
        out = args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        if pd is not None and out.suffix.lower() in (".xlsx", ".xls"):
            df = pd.DataFrame(rows)
            df.to_excel(out, index=False)
            print(f"Exporté {len(rows)} lignes dans {out}")
        else:
            # fallback CSV
            import csv
            with out.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else ["subject"])
                writer.writeheader()
                writer.writerows(rows)
            print(f"Exporté {len(rows)} lignes dans {out}")
    else:
        # Affichage rapide en console
        for r in rows[:20]:  # on tronque l'affichage
            print(r)
        if len(rows) > 20:
            print(f"... ({len(rows)-20} lignes supplémentaires)")

if __name__ == "__main__":
    main()