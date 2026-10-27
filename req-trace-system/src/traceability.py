"""Module 2 - Requirement-to-module/function/testcase mapping stored in SQLite, RTM + coverage."""
import os
import sqlite3
import pandas as pd

DB = "data/trace.db"
SEED = "data/trace_mapping.csv"


def _conn():
    return sqlite3.connect(DB)


def load_mapping():
    if not os.path.exists(DB):
        with _conn() as c:
            pd.read_csv(SEED).to_sql("mapping", c, index=False)
    with _conn() as c:
        return pd.read_sql("SELECT * FROM mapping", c)


def add_mapping(req_id, module, function, testcase, status):
    with _conn() as c:
        c.execute("INSERT INTO mapping VALUES (?,?,?,?,?)", (req_id, module, function, testcase, status))


def build_rtm(analysed, mapping):
    rtm = analysed[["Website", "Req_ID", "Type", "Priority"]].merge(mapping, on="Req_ID", how="left")
    rtm[["Module", "Function", "TestCase"]] = rtm[["Module", "Function", "TestCase"]].fillna("-")
    rtm["Status"] = rtm["Status"].fillna("Not Covered")
    return rtm


def summary(rtm):
    total = rtm.Req_ID.nunique()
    covered = rtm[rtm.TestCase != "-"].Req_ID.nunique()
    return {"total": total, "covered": covered, "coverage": round(100 * covered / total, 1) if total else 0,
            "passed": rtm[rtm.Status == "Pass"].Req_ID.nunique(), "failed": rtm[rtm.Status == "Fail"].Req_ID.nunique()}
