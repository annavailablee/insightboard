import streamlit as st
import pandas as pd
import json as _json
from src.interpreter import interpret
from src.executor import execute
from src.explainer import explain
from src.visualizer import visualize
from src.schema import profile
from src.suggestions import suggest
from src.llm_interpreter import interpret as llm_interpret

st.set_page_config(
    page_title="InsightBoard",
    page_icon="📊",
    layout="wide",
)

from src.style import inject as inject_style
inject_style()

st.markdown(
    """
    <div class="ib-hero">
      <div class="ib-hero-title"><span class="ib-hero-dot"></span>InsightBoard</div>
    </div>
    <p class="ib-hero-sub">Ask questions about your CSV in plain English.</p>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar: upload ----------
with st.sidebar:
    st.markdown("## Dataset")
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
        help="Recommended max size: 200 MB",
    )

if uploaded_file is None:
    st.markdown(
        """
        <div class="ib-empty">
            <div class="ib-empty-icon">📄</div>
            <div class="ib-empty-title">Upload a CSV to get started</div>
            <div class="ib-empty-sub">
                Use the sidebar on the left. Your data stays in your browser session.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ---------- Guardrails before loading ----------
MAX_SIZE_MB = 200
size_mb = uploaded_file.size / (1024 * 1024)

if uploaded_file.size == 0:
    st.error("The uploaded file is empty.")
    st.stop()

if size_mb > MAX_SIZE_MB:
    st.error(
        f"File is too large ({size_mb:.1f} MB). "
        f"Please upload a file under {MAX_SIZE_MB} MB."
    )
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read the CSV file: {e}")
    st.stop()

if df.empty:
    st.error("The CSV was read successfully but contains no rows.")
    st.stop()

# ---------- Sidebar: dataset info ----------
with st.sidebar:
    st.markdown(f"**{uploaded_file.name}**")
    c1, c2 = st.columns(2)
    c1.metric("Rows", f"{df.shape[0]:,}")
    c2.metric("Columns", f"{df.shape[1]:,}")

    with st.expander("Column profile"):
        prof = profile(df)
        for col, meta in prof["columns"].items():
            st.markdown(f"**{col}** — `{meta['kind']}`")
        st.divider()
    use_llm = st.toggle(
        "Use LLM interpreter",
        value=False,
        help="Requires GEMINI_API_KEY in .streamlit/secrets.toml",
    )
    profile_bytes = _json.dumps(profile(df), indent=2, default=str).encode("utf-8")
    st.download_button(
        "Download column profile (JSON)",
        data=profile_bytes,
        file_name="insightboard_profile.json",
        mime="application/json",
        key="dl_profile",
    )
    st.divider()
    st.markdown("**Try asking**")
    prof = profile(df)
    for s in suggest(df, prof):
        st.code(s, language=None)

# ---------- Main: overview ----------
st.subheader("Dataset overview")

tab_preview, tab_columns, tab_missing, tab_stats = st.tabs(
    ["Preview", "Columns & types", "Missing values", "Numeric summary"]
)

with tab_preview:
    st.dataframe(df.head(20))

with tab_columns:
    dtypes_df = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(t) for t in df.dtypes],
        "non_null": df.notna().sum().values,
        "unique": [df[c].nunique(dropna=True) for c in df.columns],
    })
    st.dataframe(dtypes_df, hide_index=True)

with tab_missing:
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        st.success("No missing values found. 🎉")
    else:
        missing_df = missing.reset_index()
        missing_df.columns = ["column", "missing_count"]
        missing_df["missing_pct"] = (
            missing_df["missing_count"] / len(df) * 100
        ).round(2)
        st.dataframe(missing_df, hide_index=True)

with tab_stats:
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        st.info("No numeric columns detected in this dataset.")
    else:
        st.dataframe(numeric_df.describe().T)

# ---------- Main: ask a question ----------
st.subheader("Ask a question")
st.caption(
    "Try: 'Which region had the highest average revenue?' "
    "or 'Top 5 products by revenue'."
)

if "history" not in st.session_state:
    st.session_state.history = []

if st.sidebar.button("Clear conversation"):
    st.session_state.history = []
    st.rerun()

question = st.text_input(
    "Your question",
    placeholder="e.g. Show revenue by category",
    key="question_input",
)

if question:
    # Avoid re-running the same question twice on rerun
    already_asked = (
        st.session_state.history
        and st.session_state.history[-1]["question"] == question
    )

    if not already_asked:
        if use_llm:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
            if not api_key:
                st.error(
                    "GEMINI_API_KEY is missing from .streamlit/secrets.toml. "
                    "Falling back to rule-based interpreter."
                )
                interp = interpret(question, df)
            else:
                with st.spinner("Thinking…"):
                    interp = llm_interpret(question, df, api_key)
        else:
            interp = interpret(question, df)

        entry = {"question": question, "interp": interp}

        if interp["status"] == "ok":
            request = interp["request"]
            outcome = execute(request, df)
            entry["request"] = request
            entry["outcome"] = outcome

            if outcome["status"] == "ok":
                entry["explanation"] = explain(request, outcome)
                entry["viz"] = visualize(request, outcome)

        st.session_state.history.append(entry)

# ---------- Render history ----------
for i, entry in enumerate(st.session_state.history):
    with st.container(border=True):
        st.markdown(
            f'<p class="ib-q">{entry["question"]}</p>',
            unsafe_allow_html=True,
        )

        interp = entry["interp"]
        if interp["status"] == "error":
            st.error(interp["message"])
            continue

        request = entry["request"]
        with st.expander("Interpreted as", expanded=False):
            st.json(request)

        outcome = entry["outcome"]
        if outcome["status"] == "error":
            st.error(outcome["message"])
            continue

        explanation = entry["explanation"]
        st.markdown('<p class="ib-label">Result</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="ib-result">{explanation["result"]}</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<p class="ib-label">Why</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="ib-why">{explanation["why"]}</p>',
            unsafe_allow_html=True,
        )

        st.dataframe(outcome["result"], hide_index=True, use_container_width=True)

        csv_bytes = outcome["result"].to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download result as CSV",
            data=csv_bytes,
            file_name=f"insightboard_result_{i + 1}.csv",
            mime="text/csv",
            key=f"dl_csv_{i}",
        )

        viz = entry.get("viz")
        if viz and viz.get("status") == "ok":
            st.markdown('<p class="ib-label">Visualization</p>',
                        unsafe_allow_html=True)
            st.plotly_chart(viz["figure"], use_container_width=True)
            st.caption(viz["reason"])