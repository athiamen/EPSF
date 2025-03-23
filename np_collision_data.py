from models import Node, Link

nodes = [
    Node(id="cause-vegetation", label="Végétation engageant le gabarit", type="cause", frequency=112.8, severity=0.8, barriers=["Entretien", "Inspection"]),
    Node(id="cause-animal", label="Animal sur la voie", type="cause", frequency=27.4, severity=0.6, barriers=["Clôture", "Signalement"]),
    Node(id="collision", label="Collision dans le gabarit", type="collision"),
    Node(id="consequence-md", label="Déversement MD", type="consequence", frequency=3.4, severity=6.0, barriers=["Détection", "CRM FU"]),
]

links = [
    Link(source="cause-vegetation", target="collision"),
    Link(source="cause-animal", target="collision"),
    Link(source="collision", target="consequence-md"),
]
