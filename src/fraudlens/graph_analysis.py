"""Privacy-safe, immutable entity graph domain records."""

from dataclasses import dataclass
from ipaddress import ip_address
import math
import re
from typing import Iterable

import networkx as nx

from fraudlens.data_contract import TRAINED_LABELS


_ENTITY_TYPES = frozenset({"phone", "upi_id", "email", "url"})
_PREDICTED_LABELS = TRAINED_LABELS | {"unknown"}
_RISK_LEVELS = frozenset({"low", "medium", "high"})
_OPAQUE_ID_RE = re.compile(r"^[0-9a-f]{64}$")
_PHONE_MASK_RE = re.compile(r"^\*{4,}\d{4}$")
_LOCAL_MASK_RE = re.compile(r"^[^@\s*]\*{3}@[A-Za-z0-9.-]+$")
_HOST_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


@dataclass(frozen=True)
class EntityLink:
    case_id: str
    created_at: str
    predicted_label: str
    risk_level: str
    risk_score: float
    entity_type: str
    entity_id: str
    masked_value: str


@dataclass(frozen=True)
class CaseNode:
    id: str
    case_id: str
    created_at: str
    predicted_label: str
    risk_level: str
    risk_score: float


@dataclass(frozen=True)
class EntityNode:
    id: str
    entity_type: str
    entity_id: str
    masked_value: str


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str


@dataclass(frozen=True)
class ConnectedComponentSummary:
    id: str
    node_ids: tuple[str, ...]
    case_count: int
    entity_count: int
    edge_count: int
    max_risk_score: float


@dataclass(frozen=True)
class EntityGraphSummary:
    case_count: int
    entity_count: int
    edge_count: int
    component_count: int
    truncated: bool


@dataclass(frozen=True)
class EntityGraphResult:
    case_nodes: tuple[CaseNode, ...]
    entity_nodes: tuple[EntityNode, ...]
    edges: tuple[GraphEdge, ...]
    components: tuple[ConnectedComponentSummary, ...]
    summary: EntityGraphSummary


@dataclass(frozen=True)
class _ValidatedLink:
    case_id: str
    created_at: str
    predicted_label: str
    risk_level: str
    risk_score: float
    entity_type: str
    entity_id: str
    masked_value: str

    @property
    def entity_key(self) -> tuple[str, str]:
        return self.entity_type, self.entity_id


def build_entity_graph(
    links: Iterable[EntityLink],
    *,
    minimum_case_count: int = 2,
    max_edges: int = 1_000,
    source_truncated: bool = False,
) -> EntityGraphResult:
    """Build a deterministic bipartite graph without exposing raw entity values."""

    _validate_options(minimum_case_count, max_edges, source_truncated)
    normalized_links = tuple(_normalize_link(link) for link in links)
    _validate_consistent_metadata(normalized_links)
    links_by_entity: dict[tuple[str, str], list[_ValidatedLink]] = {}
    for link in normalized_links:
        links_by_entity.setdefault(link.entity_key, []).append(link)

    qualifying_entities = {
        entity_key
        for entity_key, entity_links in links_by_entity.items()
        if len({link.case_id for link in entity_links}) >= minimum_case_count
    }
    unique_links = {
        (link.case_id, link.entity_type, link.entity_id): link
        for link in normalized_links
        if link.entity_key in qualifying_entities
    }
    ordered_links = tuple(unique_links[key] for key in sorted(unique_links))
    truncated = source_truncated or len(ordered_links) > max_edges
    selected_links = ordered_links[:max_edges]
    selected_case_counts = {
        entity_key: len({link.case_id for link in selected_links if link.entity_key == entity_key})
        for entity_key in qualifying_entities
    }
    selected_links = tuple(
        link
        for link in selected_links
        if selected_case_counts[link.entity_key] >= minimum_case_count
    )

    graph = nx.Graph()
    cases: dict[str, _ValidatedLink] = {}
    entities: dict[tuple[str, str], _ValidatedLink] = {}
    for link in selected_links:
        _record_consistent_case(cases, link)
        _record_consistent_entity(entities, link)
        case_node_id = _case_node_id(link.case_id)
        entity_node_id = _entity_node_id(link.entity_type, link.entity_id)
        graph.add_node(case_node_id, kind="case")
        graph.add_node(entity_node_id, kind="entity")
        graph.add_edge(case_node_id, entity_node_id)

    case_nodes = tuple(
        CaseNode(
            id=_case_node_id(link.case_id),
            case_id=link.case_id,
            created_at=link.created_at,
            predicted_label=link.predicted_label,
            risk_level=link.risk_level,
            risk_score=link.risk_score,
        )
        for _, link in sorted(cases.items())
    )
    entity_nodes = tuple(
        EntityNode(
            id=_entity_node_id(link.entity_type, link.entity_id),
            entity_type=link.entity_type,
            entity_id=link.entity_id,
            masked_value=link.masked_value,
        )
        for _, link in sorted(entities.items())
    )
    edges = tuple(
        GraphEdge(
            source=_case_node_id(link.case_id),
            target=_entity_node_id(link.entity_type, link.entity_id),
        )
        for link in selected_links
    )
    components = _summarize_components(graph, cases)
    return EntityGraphResult(
        case_nodes=case_nodes,
        entity_nodes=entity_nodes,
        edges=edges,
        components=components,
        summary=EntityGraphSummary(
            case_count=len(case_nodes),
            entity_count=len(entity_nodes),
            edge_count=len(edges),
            component_count=len(components),
            truncated=truncated,
        ),
    )


def _validate_options(minimum_case_count: int, max_edges: int, source_truncated: bool) -> None:
    if isinstance(minimum_case_count, bool) or not isinstance(minimum_case_count, int):
        raise ValueError("minimum_case_count must be an integer")
    if not 2 <= minimum_case_count <= 20:
        raise ValueError("minimum_case_count must be between 2 and 20")
    if (
        isinstance(max_edges, bool)
        or not isinstance(max_edges, int)
        or not 1 <= max_edges <= 1_000
    ):
        raise ValueError("max_edges must be an integer between one and 1,000")
    if not isinstance(source_truncated, bool):
        raise ValueError("source_truncated must be a boolean")


def _normalize_link(link: EntityLink) -> _ValidatedLink:
    if not isinstance(link, EntityLink):
        raise ValueError("links must be EntityLink records")
    case_id = _normalized_text(link.case_id, "case_id")
    created_at = _normalized_text(link.created_at, "created_at")
    predicted_label = _normalized_text(link.predicted_label, "predicted_label").casefold()
    risk_level = _normalized_text(link.risk_level, "risk_level").casefold()
    entity_type = _normalized_text(link.entity_type, "entity_type").casefold()
    entity_id = _normalized_text(link.entity_id, "entity_id").casefold()
    masked_value = _normalized_text(link.masked_value, "masked_value")
    if predicted_label not in _PREDICTED_LABELS:
        raise ValueError("predicted_label must be an approved model label")
    if risk_level not in _RISK_LEVELS:
        raise ValueError("risk_level is invalid")
    if entity_type not in _ENTITY_TYPES:
        raise ValueError("entity_type is unsupported")
    opaque_suffix = entity_id.removeprefix(entity_type + "_")
    if _OPAQUE_ID_RE.fullmatch(opaque_suffix) is None or entity_id != "{}_{}".format(
        entity_type, opaque_suffix
    ):
        raise ValueError("entity_id must be a namespaced opaque identifier")
    if not _is_masked(entity_type, masked_value):
        raise ValueError("masked_value does not match the entity type's safe mask")
    if isinstance(link.risk_score, bool) or not isinstance(link.risk_score, (int, float)):
        raise ValueError("risk_score must be numeric")
    risk_score = float(link.risk_score)
    if not math.isfinite(risk_score) or not 0.0 <= risk_score <= 100.0:
        raise ValueError("risk_score must be finite and between zero and 100")
    return _ValidatedLink(
        case_id=case_id,
        created_at=created_at,
        predicted_label=predicted_label,
        risk_level=risk_level,
        risk_score=risk_score,
        entity_type=entity_type,
        entity_id=entity_id,
        masked_value=masked_value,
    )


def _normalized_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("{} must be a non-empty string".format(name))
    return value.strip()


def _is_masked(entity_type: str, masked_value: str) -> bool:
    if entity_type == "phone":
        return _PHONE_MASK_RE.fullmatch(masked_value) is not None
    if entity_type in {"upi_id", "email"}:
        return _LOCAL_MASK_RE.fullmatch(masked_value) is not None
    return _is_safe_hostname(masked_value)


def _is_safe_hostname(value: str) -> bool:
    try:
        ip_address(value)
        return True
    except ValueError:
        pass
    if len(value) > 253 or not any(character.isalpha() for character in value):
        return False
    labels = value.split(".")
    return all(_HOST_LABEL_RE.fullmatch(label) is not None for label in labels)


def _record_consistent_case(cases: dict[str, _ValidatedLink], link: _ValidatedLink) -> None:
    existing = cases.get(link.case_id)
    if existing is None:
        cases[link.case_id] = link
    elif _case_metadata(existing) != _case_metadata(link):
        raise ValueError("case metadata must be consistent across links")


def _record_consistent_entity(
    entities: dict[tuple[str, str], _ValidatedLink], link: _ValidatedLink
) -> None:
    existing = entities.get(link.entity_key)
    if existing is None:
        entities[link.entity_key] = link
    elif existing.masked_value != link.masked_value:
        raise ValueError("entity mask must be consistent across links")


def _validate_consistent_metadata(links: tuple[_ValidatedLink, ...]) -> None:
    cases: dict[str, _ValidatedLink] = {}
    entities: dict[tuple[str, str], _ValidatedLink] = {}
    for link in links:
        _record_consistent_case(cases, link)
        _record_consistent_entity(entities, link)


def _case_metadata(link: _ValidatedLink) -> tuple[str, str, str, float]:
    return link.created_at, link.predicted_label, link.risk_level, link.risk_score


def _case_node_id(case_id: str) -> str:
    return "case:{}".format(case_id)


def _entity_node_id(entity_type: str, entity_id: str) -> str:
    return "entity:{}:{}".format(entity_type, entity_id)


def _summarize_components(
    graph: nx.Graph, cases: dict[str, _ValidatedLink]
) -> tuple[ConnectedComponentSummary, ...]:
    ordered_components = sorted(
        (tuple(sorted(component)) for component in nx.connected_components(graph)),
        key=lambda component: component,
    )
    summaries = []
    for index, node_ids in enumerate(ordered_components, start=1):
        case_node_ids = tuple(node_id for node_id in node_ids if node_id.startswith("case:"))
        entity_count = len(node_ids) - len(case_node_ids)
        max_risk_score = max(
            cases[node_id.removeprefix("case:")].risk_score for node_id in case_node_ids
        )
        summaries.append(
            ConnectedComponentSummary(
                id="component:{}".format(index),
                node_ids=node_ids,
                case_count=len(case_node_ids),
                entity_count=entity_count,
                edge_count=graph.subgraph(node_ids).number_of_edges(),
                max_risk_score=max_risk_score,
            )
        )
    return tuple(summaries)
