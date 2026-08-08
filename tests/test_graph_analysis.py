from dataclasses import asdict
import math
import random

import pytest

from fraudlens.graph_analysis import EntityLink, build_entity_graph


def _link(
    case_id="case-1",
    entity_type="phone",
    entity_id=None,
    masked_value="******1234",
    **overrides,
):
    suffix = "a" * 64
    values = {
        "case_id": case_id,
        "created_at": "2026-08-08T12:00:00Z",
        "predicted_label": "kyc_scam",
        "risk_level": "high",
        "risk_score": 90.0,
        "entity_type": entity_type,
        "entity_id": entity_id or "{}_{}".format(entity_type, suffix),
        "masked_value": masked_value,
    }
    values.update(overrides)
    return EntityLink(**values)


def test_repeated_entity_creates_a_bipartite_component():
    result = build_entity_graph([_link(), _link(case_id="case-2")])

    assert [node.id for node in result.case_nodes] == ["case:case-1", "case:case-2"]
    assert [node.id for node in result.entity_nodes] == ["entity:phone:phone_{}".format("a" * 64)]
    assert [(edge.source, edge.target) for edge in result.edges] == [
        ("case:case-1", "entity:phone:phone_{}".format("a" * 64)),
        ("case:case-2", "entity:phone:phone_{}".format("a" * 64)),
    ]
    assert len(result.components) == 1
    assert result.components[0].case_count == 2
    assert result.components[0].entity_count == 1
    assert result.components[0].edge_count == 2
    assert result.components[0].max_risk_score == 90.0
    assert result.summary.case_count == 2
    assert result.summary.entity_count == 1
    assert result.summary.edge_count == 2
    assert result.summary.component_count == 1


def test_singleton_entities_are_excluded_at_the_default_threshold():
    result = build_entity_graph([_link()])

    assert result.case_nodes == ()
    assert result.entity_nodes == ()
    assert result.edges == ()
    assert result.components == ()


def test_entity_type_namespaces_identical_opaque_suffixes():
    suffix = "b" * 64
    result = build_entity_graph(
        [
            _link(entity_id="phone_{}".format(suffix)),
            _link(case_id="case-2", entity_id="phone_{}".format(suffix)),
            _link(
                case_id="case-3",
                entity_type="email",
                entity_id="email_{}".format(suffix),
                masked_value="a***@example.test",
            ),
            _link(
                case_id="case-4",
                entity_type="email",
                entity_id="email_{}".format(suffix),
                masked_value="a***@example.test",
            ),
        ]
    )

    assert [node.id for node in result.entity_nodes] == [
        "entity:email:email_{}".format(suffix),
        "entity:phone:phone_{}".format(suffix),
    ]
    assert result.summary.entity_count == 2
    assert result.summary.component_count == 2


def test_duplicate_case_entity_rows_do_not_duplicate_edges():
    first = _link()
    result = build_entity_graph([first, first, _link(case_id="case-2")])

    assert result.summary.edge_count == 2
    assert len(result.edges) == 2


@pytest.mark.parametrize(
    ("link", "kwargs"),
    [
        (_link(entity_type="otp_like_code", entity_id="otp_like_code_{}".format("c" * 64)), {}),
        (_link(entity_id="phone_not-an-opaque-id"), {}),
        (_link(masked_value="9876501234"), {}),
        (_link(predicted_label="RAW-SENTINEL-LABEL"), {}),
        (_link(risk_score=math.nan), {}),
        (_link(risk_score=math.inf), {}),
        (_link(), {"minimum_case_count": 1}),
        (_link(), {"minimum_case_count": 21}),
        (_link(), {"max_edges": 0}),
    ],
)
def test_invalid_values_are_rejected_before_graph_building(link, kwargs):
    with pytest.raises(ValueError):
        build_entity_graph([link], **kwargs)


def test_ordering_and_component_ids_are_deterministic_across_input_order():
    links = [
        _link(case_id="case-b", entity_id="phone_{}".format("c" * 64)),
        _link(case_id="case-a", entity_id="phone_{}".format("c" * 64)),
        _link(
            case_id="case-d",
            entity_type="email",
            entity_id="email_{}".format("d" * 64),
            masked_value="d***@example.test",
        ),
        _link(
            case_id="case-c",
            entity_type="email",
            entity_id="email_{}".format("d" * 64),
            masked_value="d***@example.test",
        ),
    ]
    shuffled = list(links)
    random.Random(7).shuffle(shuffled)

    expected = asdict(build_entity_graph(links))
    actual = asdict(build_entity_graph(shuffled))

    assert actual == expected
    assert [component.id for component in build_entity_graph(links).components] == [
        "component:1",
        "component:2",
    ]


def test_edges_are_deterministically_truncated_at_the_default_cap():
    links = []
    for index in range(1_002):
        links.append(
            _link(
                case_id="case-{:04d}".format(index),
                entity_id="phone_{}".format("e" * 64),
            )
        )

    result = build_entity_graph(reversed(links))

    assert result.summary.edge_count == 1_000
    assert result.summary.truncated is True
    assert result.edges[0].source == "case:case-0000"
    assert result.edges[-1].source == "case:case-0999"


def test_truncation_removes_entities_left_below_the_case_threshold():
    result = build_entity_graph(
        [
            _link(case_id="case-1", entity_id="phone_{}".format("a" * 64)),
            _link(case_id="case-2", entity_id="phone_{}".format("b" * 64)),
            _link(case_id="case-3", entity_id="phone_{}".format("a" * 64)),
            _link(case_id="case-4", entity_id="phone_{}".format("b" * 64)),
        ],
        max_edges=3,
    )

    assert result.summary.truncated is True
    assert result.summary.edge_count == 2
    assert [node.entity_id for node in result.entity_nodes] == ["phone_{}".format("a" * 64)]
    assert [edge.source for edge in result.edges] == ["case:case-1", "case:case-3"]


def test_serialized_result_only_contains_privacy_safe_response_fields():
    raw_sentinel = "RAW-SENTINEL-DO-NOT-SERIALIZE"
    first = _link(case_id="case-1")
    object.__setattr__(first, "raw_text", raw_sentinel)
    result = build_entity_graph([first, _link(case_id="case-2")])

    serialized = asdict(result)
    assert raw_sentinel not in repr(serialized)
    assert set(serialized) == {"case_nodes", "entity_nodes", "edges", "components", "summary"}
    assert set(serialized["case_nodes"][0]) == {
        "id",
        "case_id",
        "created_at",
        "predicted_label",
        "risk_level",
        "risk_score",
    }
