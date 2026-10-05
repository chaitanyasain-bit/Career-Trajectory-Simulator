"""
Career Graph — NetworkX implementation.
Builds the graph from seed data.
"""

from __future__ import annotations

import networkx as nx


class CareerGraph:
    """
    Directed graph of career roles and transitions.

    Nodes  → career roles (normalized names)
    Edges  → possible transitions with weights
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    def add_role(self, role: str, **attrs: object) -> None:
        self._graph.add_node(role, **attrs)

    def add_transition(self, from_role: str, to_role: str, weight: float = 1.0, **attrs: object) -> None:
        self._graph.add_edge(from_role, to_role, weight=weight, **attrs)

    def get_reachable_roles(self, from_role: str, max_hops: int = 3) -> list[str]:
        """Return all roles reachable within max_hops transitions."""
        if from_role not in self._graph:
            return []
        lengths = nx.single_source_shortest_path_length(self._graph, from_role, cutoff=max_hops)
        # Exclude the starting role itself
        return [role for role in lengths if role != from_role]

    def get_path_weight(self, from_role: str, to_role: str) -> float:
        """Get shortest path transition weight product or min."""
        if from_role not in self._graph or to_role not in self._graph:
            return 0.0
        try:
            path = nx.shortest_path(self._graph, source=from_role, target=to_role)
            weight = 1.0
            for i in range(len(path) - 1):
                w = self._graph[path[i]][path[i+1]].get('weight', 0.5)
                weight *= w
            return weight
        except nx.NetworkXNoPath:
            return 0.0

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

def build_career_graph(roles: list[dict], transitions: list[dict]) -> CareerGraph:
    """Helper to construct the graph from data dictionaries."""
    cg = CareerGraph()
    for r in roles:
        cg.add_role(r["normalized_title"], title=r["title"], seniority=r["seniority_level"])

    for t in transitions:
        cg.add_transition(
            t["from"],
            t["to"],
            weight=t.get("weight", 0.5),
            months=t.get("months", 12)
        )
    return cg
