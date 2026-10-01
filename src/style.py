"""
Custom CSS for InsightBoard.
Sage palette: cream / sage / olive / dark green.
"""

CSS = """
<style>
/* ---- Hide Streamlit chrome ---- */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header [data-testid="stToolbar"] {visibility: hidden;}

/* ---- Page frame ---- */
.stApp {
    background: #FEFAE0;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1080px;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: #B2C2B2;
    border-right: 1px solid #A3B2A1;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] h2 {
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #314128 !important;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

/* ---- Typography ---- */
h1, h2, h3 {
    color: #314128;
    letter-spacing: -0.01em;
}

/* ---- Hero ---- */
.ib-hero {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 0.15rem;
}
.ib-hero-title {
    font-size: 1.9rem;
    font-weight: 700;
    color: #314128;
    letter-spacing: -0.025em;
    margin: 0;
}
.ib-hero-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    background: #87AE73;
    border-radius: 50%;
    margin-right: 0.5rem;
    transform: translateY(-3px);
}
.ib-hero-sub {
    color: #6D765B;
    font-size: 0.95rem;
    margin: 0 0 2rem 0;
    font-weight: 500;
}

/* ---- Metric cards (in sidebar → contrast on sage) ---- */
[data-testid="stMetric"] {
    background: #FEFAE0;
    border: 1px solid #A3B2A1;
    border-radius: 10px;
    padding: 0.6rem 0.9rem;
}
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6D765B !important;
    font-weight: 700;
}
[data-testid="stMetricValue"] {
    color: #314128 !important;
    font-weight: 600;
}

/* ---- File uploader ---- */
[data-testid="stFileUploaderDropzone"] {
    background: #FEFAE0 !important;
    border: 1.5px dashed #87AE73 !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"] svg {
    fill: #87AE73 !important;
    color: #87AE73 !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: #87AE73 !important;
    color: #FEFAE0 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background: #6D765B !important;
}
[data-testid="stFileUploaderDropzone"] small {
    color: #6D765B !important;
}

/* ---- Buttons ---- */
.stButton > button,
.stDownloadButton > button {
    background: transparent;
    color: #314128;
    border: 1px solid #A3B2A1;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.15s ease;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #87AE73;
    color: #314128;
    background: #FEFAE0;
}

/* ---- Inputs ---- */
.stTextInput input {
    background: #FEFAE0 !important;
    border: 1px solid #A3B2A1 !important;
    color: #314128 !important;
    border-radius: 8px !important;
}
.stTextInput input:focus {
    border-color: #87AE73 !important;
    box-shadow: 0 0 0 2px rgba(135, 174, 115, 0.25) !important;
}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 1.5rem;
    border-bottom: 1px solid #A3B2A1;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    color: #6D765B;
    padding: 0.5rem 0;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #314128 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #87AE73 !important;
}

/* ---- Result card ---- */
.ib-q {
    font-size: 1.05rem;
    font-weight: 700;
    color: #314128;
    margin: 0 0 0.75rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #B2C2B2;
}
.ib-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6D765B;
    margin: 1rem 0 0.35rem 0;
    font-weight: 700;
}
.ib-result {
    font-size: 1rem;
    color: #314128;
    line-height: 1.55;
    margin: 0;
}
.ib-why {
    font-size: 0.9rem;
    color: #6D765B;
    line-height: 1.6;
    margin: 0;
}

/* ---- Expander ---- */
[data-testid="stExpander"] {
    background: #FEFAE0;
    border: 1px solid #A3B2A1 !important;
    border-radius: 8px;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    color: #314128 !important;
    font-weight: 600;
    font-size: 0.85rem;
}

/* ---- Containers with border=True (history cards) ---- */
[data-testid="stVerticalBlockBorderWrapper"] > div > div {
    border-color: #6D765B !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FEFAE0;
    border-radius: 12px;
}

/* ---- Empty state ---- */
.ib-empty {
    border: 1.5px dashed #87AE73;
    border-radius: 14px;
    padding: 4rem 2rem;
    text-align: center;
    margin-top: 4rem;
    background: rgba(135, 174, 115, 0.08);
}
.ib-empty-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    line-height: 1;
}
.ib-empty-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #314128;
    margin-bottom: 0.35rem;
}
.ib-empty-sub {
    color: #6D765B;
    font-size: 0.9rem;
    font-weight: 500;
}

/* ---- Alerts ---- */
[data-testid="stAlert"] {
    border-radius: 10px;
}
</style>
"""


def inject():
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)