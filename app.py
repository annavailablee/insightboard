import streamlit as st
import pandas as pd
from src.interpreter import interpret
from src.executor import execute
from src.explainer import explain

st.set_page_config(
    page_title="InsightBoard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 InsightBoard")
st.caption("Ask questions about your CSV in plain English.")

# ---------- Sidebar: upload ----------
with st.sidebar:
    st.header("Dataset")
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
        help="Recommended max size: 200 MB",
    )

if uploaded_file is None:
    st.info("👈 Upload a CSV file from the sidebar to get started.")
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
    st.success(f"Loaded: {uploaded_file.name}")
    st.metric("Rows", f"{df.shape[0]:,}")
    st.metric("Columns", f"{df.shape[1]:,}")

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

question = st.text_input(
    "Your question",
    placeholder="e.g. Show revenue by category",
)

if question:
    interp = interpret(question, df)

    if interp["status"] == "error":
        st.error(interp["message"])
    else:
        request = interp["request"]

        with st.expander("Interpreted as", expanded=False):
            st.json(request)

        outcome = execute(request, df)

        if outcome["status"] == "error":
            st.error(outcome["message"])
        else:
            explanation = explain(request, outcome)

            st.markdown("**Result**")
            st.markdown(explanation["result"])

            st.markdown("**Why**")
            st.markdown(explanation["why"])

            st.dataframe(outcome["result"], hide_index=True)