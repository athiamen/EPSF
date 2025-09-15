# requirements : rdflib, pandas (facultatif pour Excel)
from rdflib import Graph, URIRef, Namespace, Literal
from collections import defaultdict
import pandas as pd
from typing import Iterable, Union, Tuple, Dict, Any, List

# ---- Utilitaires -------------------------------------------------------------

def _build_namespaces(user_prefixes: Dict[str, str]) -> Dict[str, Namespace]:
    """Construit un dict prefix -> Namespace en ajoutant des préfixes usuels."""
    defaults = {
        "rdf":   "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs":  "http://www.w3.org/2000/01/rdf-schema#",
        "owl":   "http://www.w3.org/2002/07/owl#",
        "xsd":   "http://www.w3.org/2001/XMLSchema#",
        "skos":  "http://www.w3.org/2004/02/skos/core#",
        "dcterms":"http://purl.org/dc/terms/",
        "schema":"http://schema.org/",
        "foaf":  "http://xmlns.com/foaf/0.1/",
        "sh":    "http://www.w3.org/ns/shacl#",
    }
    merged = {**defaults, **(user_prefixes or {})}
    return {p: Namespace(uri) for p, uri in merged.items()}

def _resolve_predicate(p: Union[str, URIRef, Tuple[str, str]], ns: Dict[str, Namespace]) -> URIRef:
    """Accepte URI complète, QName 'pref:term' ou tuple ('pref','term') -> URIRef."""
    if isinstance(p, URIRef):
        return p
    if isinstance(p, tuple) and len(p) == 2:
        pref, term = p
        if pref not in ns:
            raise KeyError(f"Préfixe inconnu: {pref}")
        return ns[pref][term]
    if isinstance(p, str):
        if p.startswith("http://") or p.startswith("https://"):
            return URIRef(p)
        if ":" in p:
            pref, term = p.split(":", 1)
            if pref not in ns:
                raise KeyError(f"Préfixe inconnu: {pref}")
            return ns[pref][term]
    raise TypeError(f"Format de prédicat non reconnu: {p!r}")

def _format_node(g: Graph, node, prefer_qname: bool = True) -> Any:
    """Formate proprement un objet RDF (Literal/URI/BNode) en valeur Python/str."""
    if isinstance(node, Literal):
        # Retourne la valeur native si possible (int, float, bool…), sinon str
        return node.toPython()
    if hasattr(node, "startswith"):  # petite garde
        return str(node)
    if node.__class__.__name__ == "BNode":
        return f"_:{str(node)}"
    # URIRef : tente QName (rdfs:label) sinon URI complète
    if prefer_qname:
        try:
            return g.namespace_manager.normalizeUri(node)
        except Exception:
            pass
    return str(node)

# ---- Fonction principale -----------------------------------------------------

def extract_from_ttl(
    ttl_path: str,
    predicates: Iterable[Union[str, URIRef, Tuple[str, str]]],
    prefixes: Dict[str, str] = None,
    prefer_qname: bool = True,
    collapse_single: bool = True,
    to_excel_path: str = None
) -> Dict[str, Dict[str, List[Any]]]:
    """
    Lit un TTL et extrait {sujet: {predicat: [objets...]}} pour les prédicats donnés.

    - ttl_path: chemin du fichier .ttl
    - predicates: liste de prédicats (URI, 'prefix:terme', ou ('prefix','terme'))
    - prefixes: dict des préfixes supplémentaires { 'iss': 'http://data.europa.eu/949/iss/', ... }
    - prefer_qname: True -> sujets/predicats formatés en QName quand possible
    - collapse_single: True -> liste à 1 élément aplatie lors de l’export DataFrame/Excel
    - to_excel_path: si fourni, crée un Excel avec une ligne par sujet
    """
    g = Graph()
    g.parse(ttl_path, format="turtle")

    # Construire et binder les namespaces
    ns = _build_namespaces(prefixes or {})
    for p, n in ns.items():
        g.bind(p, n)

    # Résoudre les prédicats
    pred_uris = [(p, _resolve_predicate(p, ns)) for p in predicates]

    # data[sujet][predicat] -> set(objets)
    data = defaultdict(lambda: defaultdict(set))

    for p_raw, p_uri in pred_uris:
        for s, o in g.subject_objects(p_uri):
            s_key = _format_node(g, s, prefer_qname=prefer_qname)
            p_key = _format_node(g, p_uri, prefer_qname=prefer_qname)
            o_val = _format_node(g, o, prefer_qname=prefer_qname)
            data[s_key][p_key].add(o_val)

    # Convertir les sets en listes triées (stable)
    result = {
        s: {p: sorted(list(vals), key=lambda x: str(x)) for p, vals in preds.items()}
        for s, preds in data.items()
    }

    # Optionnel : export Excel (une ligne par sujet, cellules ' | ' pour multi-valeurs)
    if to_excel_path:
        # Colonnes = union des prédicats rencontrés
        all_preds = sorted({p for preds in result.values() for p in preds.keys()})
        rows = []
        for s, preds in result.items():
            row = {"subject": s}
            for p in all_preds:
                vals = preds.get(p, [])
                if collapse_single and len(vals) == 1:
                    row[p] = vals[0]
                else:
                    row[p] = " | ".join(map(str, vals))
            rows.append(row)
        df = pd.DataFrame(rows, columns=["subject"] + all_preds)
        # Conserver l’ordre et écrire
        with pd.ExcelWriter(to_excel_path, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="extraction")

    return result