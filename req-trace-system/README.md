# Automated Software Requirements Analysis, Conflict Detection and Traceability System

Team project with two modules.

| Member | Module | Techniques |
|---|---|---|
| S. Yaso Priya | Requirements analysis & conflict detection (classification, ambiguity, completeness, conflicts) | Rule-based analysis, keyword matching, TF-IDF text similarity |
| C. A. Nandhana | Traceability & analysis dashboard (requirement -> module -> function -> test case) | RTM, SQLite mapping, Plotly visualization |

Sample websites: **ShopEasy** (e-commerce) and **SchoolPro** (school management).

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Upload your own CSV with columns `Website, Req_ID, Requirement, Priority`.

## Structure
```
app.py                  # Streamlit dashboard
src/analyzer.py         # Module 1
src/traceability.py     # Module 2
data/                   # sample requirements + trace mapping
```
