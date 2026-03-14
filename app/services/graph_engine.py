"""
app/services/graph_engine.py
-----------------------------
Skill Graph Engine — Feature #1

Builds a directed graph:  Subject → Skill → Career

Uses NetworkX under the hood. The graph is constructed fresh from the
database on each call (suitable for a hackathon; add Redis caching for
production scale).

The returned payload is node-link JSON — the exact format expected by
D3.js force-directed graphs.
"""

import networkx as nx
from sqlalchemy.orm import Session

from app.models.orm import Career, CareerSkill, Skill, Subject
from app.schemas.schemas import GraphEdge, GraphNode, SkillGraphResponse


class SkillGraphEngine:
    """Constructs and serialises the skill graph for a given career."""

    # Node-type prefixes keep IDs unique across types
    SUBJECT_PREFIX = "subject_"
    SKILL_PREFIX   = "skill_"
    CAREER_PREFIX  = "career_"

    def build_graph(self, db: Session, career_id: int) -> SkillGraphResponse:
        """
        1. Load the career and all its required skills from the DB.
        2. For each skill, also load the parent subject if available.
        3. Populate a NetworkX DiGraph with typed nodes and weighted edges.
        4. Serialise to node-link format.
        """
        # --- Fetch data --------------------------------------------------
        career: Career | None = db.query(Career).filter(Career.id == career_id).first()
        if career is None:
            raise ValueError(f"Career {career_id} not found")

        career_skills: list[CareerSkill] = (
            db.query(CareerSkill)
            .filter(CareerSkill.career_id == career_id)
            .all()
        )

        # --- Build graph -------------------------------------------------
        G = nx.DiGraph()

        # Career node
        career_node_id = f"{self.CAREER_PREFIX}{career.id}"
        G.add_node(career_node_id, label=career.title, type="career")

        seen_subjects: set[int] = set()

        for cs in career_skills:
            skill: Skill = cs.skill

            # Skill node
            skill_node_id = f"{self.SKILL_PREFIX}{skill.id}"
            G.add_node(skill_node_id, label=skill.name, type="skill")

            # Skill → Career edge (weight = importance of skill to this career)
            G.add_edge(skill_node_id, career_node_id, weight=cs.weight)

            # Subject → Skill edge (only if subject exists and not yet added)
            if skill.subject_id and skill.subject_id not in seen_subjects:
                subject: Subject = skill.subject
                subject_node_id = f"{self.SUBJECT_PREFIX}{subject.id}"
                G.add_node(subject_node_id, label=subject.name, type="subject")
                seen_subjects.add(skill.subject_id)

            if skill.subject_id:
                subject_node_id = f"{self.SUBJECT_PREFIX}{skill.subject_id}"
                if not G.has_edge(subject_node_id, skill_node_id):
                    G.add_edge(subject_node_id, skill_node_id, weight=1.0)

        # --- Serialise ---------------------------------------------------
        nodes = [
            GraphNode(id=n, label=data["label"], type=data["type"])
            for n, data in G.nodes(data=True)
        ]

        links = [
            GraphEdge(
                source=u,
                target=v,
                weight=data.get("weight", 1.0),
            )
            for u, v, data in G.edges(data=True)
        ]

        return SkillGraphResponse(career_id=career_id, nodes=nodes, links=links)
