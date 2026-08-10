from dataclasses import replace

import pytest

from fraudlens.data_contract import TRAINED_LABELS
from fraudlens.graph_analysis import EntityLink, build_entity_graph


_CLASSIFICATIONS = (
    ("kyc_scam", "KYC scam"),
    ("digital_arrest", "Digital arrest"),
    ("fake_job", "Fake job"),
    ("investment_scam", "Investment scam"),
    ("loan_scam", "Loan scam"),
    ("courier_scam", "Courier scam"),
    ("upi_refund_scam", "UPI refund scam"),
    ("otp_phishing", "OTP phishing"),
    ("legitimate", "Legitimate"),
    ("unknown", "Unknown"),
)


def _result():
    entity_id = "phone_" + "a" * 64
    return build_entity_graph(
        [
            EntityLink(
                case_id="case-one",
                created_at="2026-08-08T12:00:00Z",
                predicted_label="kyc_scam",
                risk_level="high",
                risk_score=91.0,
                entity_type="phone",
                entity_id=entity_id,
                masked_value="******1234",
            ),
            EntityLink(
                case_id="case-two",
                created_at="2026-08-08T12:05:00Z",
                predicted_label="kyc_scam",
                risk_level="medium",
                risk_score=72.0,
                entity_type="phone",
                entity_id=entity_id,
                masked_value="******1234",
            ),
        ]
    )


def test_graph_view_exposes_only_safe_metrics_and_investigation_tables():
    from fraudlens.graph_dashboard import build_graph_view

    view = build_graph_view(_result())

    assert view.metrics.case_count == 2
    assert view.metrics.entity_count == 1
    assert view.metrics.edge_count == 2
    assert view.metrics.component_count == 1
    assert view.metrics.truncated is False
    assert view.entity_rows == (
        {
            "Evidence hub": "******1234",
            "Type": "Phone",
            "Linked incidents": 2,
        },
    )
    assert view.component_rows == (
        {
            "Cluster": "Cluster 1",
            "Incidents": 2,
            "Evidence hubs": 1,
            "Links": 2,
            "Highest risk": "91.0",
        },
    )
    assert "Incident 1" in view.dot
    assert "KYC scam" in view.dot
    assert "High risk" in view.dot
    assert "******1234" in view.dot
    assert "case-one" not in view.dot
    assert "phone_" not in view.dot
    assert '  "case_1" [label="Incident 1\\nKYC scam · High risk", shape="box"];' in view.dot


def test_graph_view_escapes_dot_labels_and_fails_closed_for_unmasked_values():
    from fraudlens.graph_dashboard import build_graph_view

    result = _result()
    unsafe_entity = replace(
        result.entity_nodes[0], masked_value='RAW_SENTINEL " slash\\\nnew line'
    )
    view = build_graph_view(replace(result, entity_nodes=(unsafe_entity,)))

    assert "RAW_SENTINEL" not in view.dot
    assert "RAW_SENTINEL" not in str(view.entity_rows)
    assert 'label="Masked identifier"' in view.dot
    assert "\\\"" not in view.dot
    assert "slash\\" not in view.dot
    assert "\nnew line" not in view.dot


def test_dot_escape_quotes_backslashes_and_newlines_without_creating_dot_syntax():
    from fraudlens.graph_dashboard import escape_dot_label

    assert escape_dot_label('a"b\\c\nd') == 'a\\"b\\\\c\\nd'


@pytest.mark.parametrize(
    ("label", "readable_label"),
    _CLASSIFICATIONS,
)
def test_graph_view_displays_every_canonical_classification(label, readable_label):
    from fraudlens.graph_dashboard import build_graph_view

    assert {classification for classification, _ in _CLASSIFICATIONS} == TRAINED_LABELS | {"unknown"}
    result = _result()
    labeled_cases = tuple(replace(case, predicted_label=label) for case in result.case_nodes)

    assert readable_label in build_graph_view(replace(result, case_nodes=labeled_cases)).dot


@pytest.mark.parametrize("masked_value", ["192.0.2.1", "2001:db8::1", "kyc-login.example"])
def test_graph_view_keeps_valid_url_masks(masked_value):
    from fraudlens.graph_dashboard import build_graph_view

    result = _result()
    url_node = replace(result.entity_nodes[0], entity_type="url", masked_value=masked_value)

    assert masked_value in build_graph_view(replace(result, entity_nodes=(url_node,))).dot


@pytest.mark.parametrize(
    "raw_value",
    [
        "9876543210",
        "dead:beef",
        "raw-secret.example/path",
        "fe80::1%RAW_SENTINEL",
        ".".join(character * 63 for character in "abcd"),
    ],
)
def test_graph_view_hides_invalid_url_masks(raw_value):
    from fraudlens.graph_dashboard import build_graph_view

    result = _result()
    url_node = replace(result.entity_nodes[0], entity_type="url", masked_value=raw_value)
    view = build_graph_view(replace(result, entity_nodes=(url_node,)))

    assert raw_value not in view.dot
    assert raw_value not in str(view.entity_rows)
    assert "Masked identifier" in view.dot


def test_graph_dashboard_import_does_not_open_or_read_case_storage(monkeypatch):
    import importlib
    import sys

    from fraudlens import analysis_service

    constructor_calls = []

    class _ForbiddenStore:
        def __init__(self, *args, **kwargs):
            constructor_calls.append((args, kwargs))
            raise AssertionError("dashboard import must not open storage")

    monkeypatch.setattr(analysis_service, "DatabaseCaseStore", _ForbiddenStore)
    sys.modules.pop("fraudlens.dashboard", None)
    dashboard = importlib.import_module("fraudlens.dashboard")

    assert constructor_calls == []
    monkeypatch.undo()
    importlib.reload(dashboard)


def test_dashboard_reads_graph_storage_only_after_an_explicit_refresh(monkeypatch):
    from fraudlens import dashboard

    class _Streamlit:
        def __init__(self, refresh):
            self.refresh = refresh
            self.session_state = {}

        def selectbox(self, *args, **kwargs):
            return 2

        def button(self, label, **kwargs):
            return self.refresh and label == "Refresh Graph"

        def caption(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

        def columns(self, count):
            return [self] * count

        def metric(self, *args, **kwargs):
            pass

        def markdown(self, *args, **kwargs):
            pass

        def subheader(self, *args, **kwargs):
            pass

        def graphviz_chart(self, *args, **kwargs):
            pass

    class _Store:
        def __init__(self):
            self.calls = []

        def entity_graph(self, **kwargs):
            self.calls.append(kwargs)
            return _result()

    store = _Store()
    monkeypatch.setattr(dashboard, "st", _Streamlit(refresh=False))
    dashboard._render_entity_graph_tab(store)
    assert store.calls == []

    monkeypatch.setattr(dashboard, "st", _Streamlit(refresh=True))
    dashboard._render_entity_graph_tab(store)
    assert store.calls == [{"minimum_case_count": 2, "case_limit": 100, "max_edges": 1_000}]


def test_dashboard_hides_stale_graphs_and_clears_them_after_refresh_failure(monkeypatch):
    from fraudlens import dashboard

    class _Streamlit:
        def __init__(self):
            self.session_state = {}
            self.refresh = True
            self.threshold = 2
            self.graphs = []
            self.errors = []

        def selectbox(self, *args, **kwargs):
            return self.threshold

        def button(self, *args, **kwargs):
            return self.refresh

        def caption(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

        def error(self, message):
            self.errors.append(message)

        def columns(self, count):
            return [self] * count

        def metric(self, *args, **kwargs):
            pass

        def markdown(self, *args, **kwargs):
            pass

        def subheader(self, *args, **kwargs):
            pass

        def graphviz_chart(self, dot, **kwargs):
            self.graphs.append(dot)

    class _Store:
        def __init__(self):
            self.fail = False

        def entity_graph(self, **kwargs):
            if self.fail:
                raise RuntimeError("private graph failure")
            return _result()

    streamlit = _Streamlit()
    store = _Store()
    monkeypatch.setattr(dashboard, "st", streamlit)
    dashboard._render_entity_graph_tab(store)
    assert streamlit.graphs

    streamlit.refresh = False
    streamlit.threshold = 3
    dashboard._render_entity_graph_tab(store)
    assert len(streamlit.graphs) == 1

    streamlit.refresh = True
    store.fail = True
    dashboard._render_entity_graph_tab(store)
    assert "entity_graph_view" not in streamlit.session_state
    assert "entity_graph_threshold" not in streamlit.session_state
    assert streamlit.errors == ["Entity graph could not be loaded. Try refreshing again."]
