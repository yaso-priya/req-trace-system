import pandas as pd
import plotly.express as px
import streamlit as st
from src.analyzer import analyze
from src import traceability as tr

st.set_page_config(page_title="Requirements Analysis & Traceability", layout="wide")
st.title("Automated Software Requirements Analysis, Conflict Detection & Traceability System")

page = st.sidebar.radio("Go to", ["1. Requirement Analysis", "2. Conflict Detection",
                                  "3. Traceability Matrix", "4. Dashboard & Report"])
up = st.sidebar.file_uploader("Upload requirements CSV", type="csv",
                              help="Columns: Website, Req_ID, Requirement, Priority")
req = pd.read_csv(up) if up else pd.read_csv("data/sample_requirements.csv")
site = st.sidebar.selectbox("Website", ["All"] + sorted(req.Website.unique()))
if site != "All":
    req = req[req.Website == site]

analysed, conflicts = analyze(req)
mapping = tr.load_mapping()
rtm = tr.build_rtm(analysed, mapping)
stats = tr.summary(rtm)

if page.startswith("1"):
    st.subheader("Requirement collection, classification, ambiguity & completeness")
    st.dataframe(analysed, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total requirements", len(analysed))
    c2.metric("Ambiguous", int((analysed.Ambiguity != "Clear").sum()))
    c3.metric("Incomplete", int((analysed.Completeness != "Complete").sum()))

elif page.startswith("2"):
    st.subheader("Detected conflicts")
    if conflicts.empty:
        st.success("No conflicts found.")
    else:
        st.dataframe(conflicts, use_container_width=True)
        st.plotly_chart(px.histogram(conflicts, x="Conflict_Type", color="Severity", title="Conflicts by type & severity"))

elif page.startswith("3"):
    st.subheader("Requirements Traceability Matrix (Requirement -> Module -> Function -> Test case)")
    st.dataframe(rtm, use_container_width=True)
    with st.expander("Add a new mapping"):
        with st.form("add"):
            rid = st.selectbox("Req_ID", analysed.Req_ID)
            m, f, t = st.text_input("Module"), st.text_input("Function"), st.text_input("TestCase")
            s = st.selectbox("Status", ["Pass", "Fail", "Not Run"])
            if st.form_submit_button("Save") and m and t:
                tr.add_mapping(rid, m, f, t, s)
                st.success("Saved. Refresh the page to see it.")

else:
    st.subheader("Dashboard")
    c = st.columns(4)
    c[0].metric("Requirements", stats["total"])
    c[1].metric("Test coverage", f'{stats["coverage"]}%')
    c[2].metric("Tests passed", stats["passed"])
    c[3].metric("Tests failed", stats["failed"])
    a, b = st.columns(2)
    a.plotly_chart(px.pie(rtm, names="Status", title="Test status"), use_container_width=True)
    b.plotly_chart(px.histogram(analysed, x="Category", color="Priority", title="Requirement types"),
                   use_container_width=True)
    st.download_button("Download RTM report (CSV)", rtm.to_csv(index=False), "rtm_report.csv")
    st.download_button("Download conflict report (CSV)", conflicts.to_csv(index=False), "conflict_report.csv")
