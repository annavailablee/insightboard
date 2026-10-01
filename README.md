# InsightBoard

Ask questions about your CSV in plain English — get answers, charts, and explanations.

![InsightBoard screenshot](docs/screenshot.png)

## What it does

- Upload a CSV and see an automatic dataset overview (shape, dtypes, missing values, numeric summary)
- Ask questions like "Which region had the highest average revenue?" or "Show revenue by month"
- The app interprets the question, runs a real pandas operation, and returns a table, a chart, and a plain-English explanation
- Suggested questions are generated from the schema so you always know what's possible
- Every result is downloadable as CSV; the schema is downloadable as JSON
- Works with a rule-based interpreter by default, or an LLM interpreter (Gemini) for flexible phrasing

## Architecture

The core design principle: **the LLM never executes code**. It only produces a structured JSON request describing the intended analysis. Python validates that request and executes it with pandas.

User question
↓
interpreter.py (rule-based OR llm_interpreter.py)
↓ produces {operation, group_by, metric, aggregation, ...}
executor.py — validates the request, runs pandas
↓
explainer.py — turns (request, result) into plain English
visualizer.py — picks a chart type from the request shape
↓
Streamlit UI


Why this matters:

- **Safety**: no arbitrary code execution, ever. The LLM's output is treated as untrusted input.
- **Testability**: the executor can be unit-tested with hand-written request dicts, no LLM involved.
- **Swappability**: replacing the interpreter doesn't touch the executor, explainer, or visualizer.

## Tech stack

- **Python**, **Streamlit** (UI)
- **pandas**, **NumPy** (data)
- **Plotly** (charts)
- **Google Gemini API** (natural-language interpretation)
- **Git/GitHub**

## How to run locally

```bash
git clone https://github.com/YOUR_USERNAME/insightboard.git
cd insightboard
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py