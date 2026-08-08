"""Pure, privacy-safe presentation adapter for the entity graph dashboard."""

from dataclasses import dataclass
from ipaddress import ip_address
import re

from fraudlens.graph_analysis import EntityGraphResult


_ENTITY_TYPE_LABELS = {
    "phone": "Phone",
    "upi_id": "UPI ID",
    "email": "Email",
    "url": "URL",
}
_CLASSIFICATION_LABELS = {
    "kyc_scam": "KYC scam",
    "digital_arrest": "Digital arrest",
    "fake_job": "Fake job",
    "investment_scam": "Investment scam",
    "loan_scam": "Loan scam",
    "courier_scam": "Courier scam",
    "upi_refund_scam": "UPI refund scam",
    "otp_phishing": "OTP phishing",
    "legitimate": "Legitimate",
    "unknown": "Unknown",
}
_RISK_LABELS = {"low": "Low", "medium": "Medium", "high": "High"}
_PHONE_MASK_RE = re.compile(r"^\*{4,}\d{4}$")
_LOCAL_MASK_RE = re.compile(r"^[^@\s*]\*{3}@[A-Za-z0-9.-]+$")
_HOST_MASK_RE = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$"
)


@dataclass(frozen=True)
class GraphMetrics:
    case_count: int
    entity_count: int
    edge_count: int
    component_count: int
    truncated: bool


@dataclass(frozen=True)
class GraphView:
    """Dashboard-ready graph evidence without raw identifiers or case IDs."""

    metrics: GraphMetrics
    entity_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    dot: str


def build_graph_view(result: EntityGraphResult) -> GraphView:
    """Adapt a validated graph result into safe tables and Graphviz DOT."""

    entity_ids = {node.id: "entity_{}".format(index) for index, node in enumerate(result.entity_nodes, 1)}
    case_ids = {node.id: "case_{}".format(index) for index, node in enumerate(result.case_nodes, 1)}
    linked_incidents = {node.id: 0 for node in result.entity_nodes}
    for edge in result.edges:
        if edge.target in linked_incidents and edge.source in case_ids:
            linked_incidents[edge.target] += 1

    entity_rows = tuple(
        {
            "Evidence hub": _safe_masked_value(node.entity_type, node.masked_value),
            "Type": _ENTITY_TYPE_LABELS.get(node.entity_type, "Masked identifier"),
            "Linked incidents": linked_incidents[node.id],
        }
        for node in result.entity_nodes
    )
    component_rows = tuple(
        {
            "Cluster": "Cluster {}".format(index),
            "Incidents": component.case_count,
            "Evidence hubs": component.entity_count,
            "Links": component.edge_count,
            "Highest risk": "{:.1f}".format(component.max_risk_score),
        }
        for index, component in enumerate(result.components, 1)
    )
    return GraphView(
        metrics=GraphMetrics(
            case_count=result.summary.case_count,
            entity_count=result.summary.entity_count,
            edge_count=result.summary.edge_count,
            component_count=result.summary.component_count,
            truncated=result.summary.truncated,
        ),
        entity_rows=entity_rows,
        component_rows=component_rows,
        dot=_build_dot(result, case_ids, entity_ids),
    )


def escape_dot_label(value: str) -> str:
    """Escape text for a quoted Graphviz label without introducing markup."""

    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def _build_dot(
    result: EntityGraphResult, case_ids: dict[str, str], entity_ids: dict[str, str]
) -> str:
    lines = [
        "graph EntityGraph {",
        '  graph [bgcolor="transparent", rankdir="LR"];',
        '  node [style="filled", fillcolor="white"];',
    ]
    for node in result.entity_nodes:
        label = _safe_masked_value(node.entity_type, node.masked_value)
        lines.append(
            '  "{}" [label="{}", shape="ellipse"];'.format(
                entity_ids[node.id], escape_dot_label(label)
            )
        )
    for index, node in enumerate(result.case_nodes, 1):
        classification = _CLASSIFICATION_LABELS.get(node.predicted_label, "Unknown")
        risk = _RISK_LABELS.get(node.risk_level, "Unknown")
        label = "Incident {}\n{} · {} risk".format(index, classification, risk)
        lines.append(
            '  "{}" [label="{}", shape="box"];'.format(
                case_ids[node.id], escape_dot_label(label)
            )
        )
    for edge in result.edges:
        source = case_ids.get(edge.source)
        target = entity_ids.get(edge.target)
        if source is not None and target is not None:
            lines.append('  "{}" -- "{}";'.format(source, target))
    lines.append("}")
    return "\n".join(lines)


def _safe_masked_value(entity_type: str, masked_value: str) -> str:
    if not isinstance(masked_value, str):
        return "Masked identifier"
    if entity_type == "phone" and _PHONE_MASK_RE.fullmatch(masked_value):
        return masked_value
    if entity_type in {"upi_id", "email"} and _LOCAL_MASK_RE.fullmatch(masked_value):
        return masked_value
    if entity_type == "url":
        try:
            ip_address(masked_value)
            return masked_value
        except ValueError:
            if _HOST_MASK_RE.fullmatch(masked_value) and any(
                character.isalpha() for character in masked_value
            ):
                return masked_value
    return "Masked identifier"
