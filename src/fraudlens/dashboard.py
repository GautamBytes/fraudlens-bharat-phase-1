import pandas as pd
import streamlit as st

from fraudlens.analysis_service import AnalysisInput, DatabaseCaseStore, create_analysis_service
from fraudlens.dashboard_workflow import analyze_uploaded_file
from fraudlens.graph_dashboard import build_graph_view
from fraudlens.image_analysis import ImageAnalysisService
from fraudlens.ocr import OcrService
from fraudlens.settings import Settings


DEMO_MESSAGES = {
    "Fake KYC SMS": "Dear customer your bank KYC is expired. Update PAN at http://bank-kyc-verify.example/login or account will block today.",
    "OTP Phishing": "Login attempt detected. Send OTP code 482913 to verify ur identity or account delete ho jayega.",
    "Fake Job Scam": "Work from home job hai, salary 45000 monthly. Joining kit fee Rs 999 send karo to hr@jobpay.example.",
    "Investment Scam": "Join crypto VIP group. Guaranteed 15 percent profit daily. Invest 5000 now and double in 7 days.",
}


def _result_to_dict(result):
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return result.dict()


@st.cache_resource
def _analysis_dependencies():
    settings = Settings.from_env()
    case_store = DatabaseCaseStore(
        settings.database_path,
        hmac_secret=settings.hmac_secret,
        retention_days=settings.retention_days,
    )
    analysis_service = create_analysis_service(settings=settings, store=case_store)
    ocr_service = OcrService()
    image_analysis_service = ImageAnalysisService(ocr_service, analysis_service)
    return analysis_service, image_analysis_service, case_store


def _render_result(result):
    metric_cols = st.columns(4)
    metric_cols[0].metric("Fraud Type", result["predicted_label"])
    metric_cols[1].metric("Risk Level", result["risk_level"].upper())
    metric_cols[2].metric("Confidence", f"{result['confidence']:.2f}")
    metric_cols[3].metric("Risk Score", f"{result['risk_score']:.1f}/100")

    metadata = result.get("metadata", {})
    st.caption(
        "Model: {} | Abstained: {} | Stored: {}".format(
            metadata.get("prediction_model_version", "unknown"),
            metadata.get("prediction_abstained", False),
            metadata.get("stored", False),
        )
    )

    if metadata.get("input_source") == "image":
        st.subheader("Extracted OCR Text")
        st.code(result.get("original_text", ""), language="text")
        st.caption(
            "Input source: image | OCR engine: {} | OCR languages: {} | Image dimensions: {} x {}".format(
                metadata.get("ocr_engine", "unknown"),
                metadata.get("ocr_languages", "unknown"),
                metadata.get("ocr_width", "unknown"),
                metadata.get("ocr_height", "unknown"),
            )
        )

    left, right = st.columns([1.1, 0.9])
    with left:
        st.subheader("Extracted Evidence")
        entities = result.get("entities", [])
        if entities:
            st.dataframe(pd.DataFrame(entities), use_container_width=True)
        else:
            st.info("No structured entities detected.")

        st.subheader("Explanation")
        for item in result.get("explanation", []):
            st.write(f"- {item}")

    with right:
        st.subheader("Complaint Draft")
        st.code(result["complaint_draft"], language="text")

        st.subheader("Risk Signals")
        signals = result.get("risk_signals", [])
        if signals:
            st.dataframe(pd.DataFrame(signals), use_container_width=True)
        if metadata.get("storage_warning"):
            st.warning(metadata["storage_warning"])


def _render_entity_graph_tab(case_store):
    """Render stored relationship evidence only after the investigator refreshes it."""

    minimum_case_count = st.selectbox(
        "Repeated incident threshold",
        options=list(range(2, 21)),
        index=0,
        help="Show evidence hubs linked to at least this many stored incidents.",
    )
    st.caption(
        "Evidence hubs use masked identifiers. Cases are shown as linked incidents; "
        "raw messages and raw entity values are never displayed."
    )
    if st.button("Refresh Graph", type="primary"):
        try:
            graph_result = case_store.entity_graph(
                minimum_case_count=minimum_case_count,
                case_limit=100,
                max_edges=1_000,
            )
            st.session_state["entity_graph_view"] = build_graph_view(graph_result)
            st.session_state["entity_graph_threshold"] = minimum_case_count
        except Exception:
            st.session_state.pop("entity_graph_view", None)
            st.session_state.pop("entity_graph_threshold", None)
            st.error("Entity graph could not be loaded. Try refreshing again.")
            return

    graph_view = st.session_state.get("entity_graph_view")
    if (
        graph_view is None
        or st.session_state.get("entity_graph_threshold") != minimum_case_count
    ):
        st.info("Choose a threshold, then select Refresh Graph to inspect repeated evidence.")
        return

    metrics = graph_view.metrics
    metric_cols = st.columns(4)
    metric_cols[0].metric("Linked incidents", metrics.case_count)
    metric_cols[1].metric("Evidence hubs", metrics.entity_count)
    metric_cols[2].metric("Links", metrics.edge_count)
    metric_cols[3].metric("Clusters", metrics.component_count)
    if metrics.truncated:
        st.warning("This graph is truncated to the safe display limit. Narrow the investigation.")
    if metrics.edge_count == 0:
        st.info(
            "No repeated evidence meets this threshold. Store more consented analyses or lower the threshold."
        )
        return

    st.graphviz_chart(graph_view.dot, use_container_width=True)
    st.subheader("Evidence hubs")
    st.dataframe(pd.DataFrame(graph_view.entity_rows), use_container_width=True)
    st.subheader("Linked incident clusters")
    st.dataframe(pd.DataFrame(graph_view.component_rows), use_container_width=True)


def main():
    st.set_page_config(page_title="FraudLens Bharat", page_icon="FL", layout="wide")
    st.title("FraudLens Bharat")
    st.caption("Phase 1 baseline prototype for Hinglish cyber-fraud triage")

    if "message_text" not in st.session_state:
        st.session_state.message_text = DEMO_MESSAGES["Fake KYC SMS"]

    store_case = st.checkbox("Store this analysis locally", value=False)
    text_tab, screenshot_tab, graph_tab = st.tabs(["Text", "Screenshot", "Entity Graph"])

    with text_tab:
        demo_cols = st.columns(4)
        for index, (label, message) in enumerate(DEMO_MESSAGES.items()):
            if demo_cols[index].button(label, use_container_width=True):
                st.session_state.message_text = message

        message = st.text_area(
            "Suspicious message",
            key="message_text",
            height=180,
        )
        if st.button("Analyze Message", type="primary"):
            analysis_service, _, _ = _analysis_dependencies()
            result = analysis_service.analyze(
                AnalysisInput(text=message, store_case=store_case)
            )
            st.session_state.last_result = _result_to_dict(result)
            st.session_state.pop("screenshot_error", None)

    with screenshot_tab:
        uploaded_file = st.file_uploader(
            "Upload a screenshot",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
            max_upload_size=5,
        )
        if st.button("Analyze Screenshot", type="primary"):
            if uploaded_file is None:
                st.warning("Choose a PNG or JPEG screenshot before analyzing.")
            else:
                _, image_analysis_service, _ = _analysis_dependencies()
                outcome = analyze_uploaded_file(
                    image_analysis_service,
                    uploaded_file=uploaded_file,
                    store_case=store_case,
                )
                if outcome.error_message:
                    st.session_state.pop("last_result", None)
                    st.session_state.screenshot_error = outcome.error_message
                else:
                    st.session_state.last_result = _result_to_dict(outcome.result)
                    st.session_state.pop("screenshot_error", None)

    with graph_tab:
        _, _, case_store = _analysis_dependencies()
        _render_entity_graph_tab(case_store)

    if "screenshot_error" in st.session_state:
        st.error(st.session_state.screenshot_error)
    if "last_result" in st.session_state:
        _render_result(st.session_state.last_result)

    st.divider()
    st.subheader("Recent Analysis History")
    _, _, case_store = _analysis_dependencies()
    recent_cases = case_store.list_cases(limit=10)
    if recent_cases:
        st.dataframe(pd.DataFrame(recent_cases), use_container_width=True)
    else:
        st.info("No cases analyzed yet.")


if __name__ == "__main__":
    main()
