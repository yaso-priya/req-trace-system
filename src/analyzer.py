"""Module 1 - Requirement analysis & conflict detection (rule-based + keyword matching + TF-IDF text similarity)."""
import re
from itertools import combinations
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

NFR_KEYWORDS = {
    "Performance": ["within", "seconds", "fast", "concurrent", "response time", "load", "throughput"],
    "Security": ["encrypt", "password", "private", "secure", "authenticate", "authorization", "access"],
    "Usability": ["easy", "user-friendly", "intuitive", "accessible", "usable"],
    "Reliability": ["available", "uptime", "backup", "recover", "timeout"],
    "Compatibility": ["browser", "mobile", "platform", "compatible"],
}
VAGUE_WORDS = ["fast", "easy", "user-friendly", "appropriate", "various", "etc", "as needed", "flexible",
               "efficient", "good", "robust", "simple", "quickly", "and/or", "tbd", "some", "many"]
MODALS = ["shall", "must", "should", "will", "may", "can"]
OPPOSITES = [("allow guest", "require users to login"), ("without creating an account", "login before"),
             ("only teachers", "allow clerks"), ("visible only to", "visible to all"),
             ("enable", "disable"), ("public", "private"), ("real-time", "batch")]
UNIT_RE = re.compile(r"(\d[\d,]*)\s*(seconds?|minutes?|hours?|days?|concurrent users|users|%)", re.I)


def classify(text):
    t = text.lower()
    for cat, words in NFR_KEYWORDS.items():
        if any(w in t for w in words):
            return "Non-Functional", cat
    return "Functional", "Functional"


def ambiguity(text):
    t = text.lower()
    return [w for w in VAGUE_WORDS if re.search(r"\b" + re.escape(w) + r"\b", t)]


def completeness(text, rtype):
    issues = []
    t = text.lower()
    if not any(re.search(rf"\b{m}\b", t) for m in MODALS):
        issues.append("no shall/must/should")
    if len(text.split()) < 6:
        issues.append("too short")
    if rtype == "Non-Functional" and not re.search(r"\d", t):
        issues.append("not measurable (no number)")
    if "tbd" in t:
        issues.append("contains TBD")
    return issues


def _numbers(text):
    out = {}
    for n, u in UNIT_RE.findall(text):
        out.setdefault(u.lower().rstrip("s"), set()).add(n.replace(",", ""))
    return out


def analyze(df):
    df = df.copy().reset_index(drop=True)
    rows = []
    for _, r in df.iterrows():
        rtype, cat = classify(r.Requirement)
        amb, inc = ambiguity(r.Requirement), completeness(r.Requirement, rtype)
        rows.append({**r.to_dict(), "Type": rtype, "Category": cat,
                     "Ambiguity": ", ".join(amb) or "Clear",
                     "Completeness": "Complete" if not inc else "Incomplete: " + "; ".join(inc)})
    return pd.DataFrame(rows), detect_conflicts(df)


def detect_conflicts(df):
    out = []
    for site, g in df.groupby("Website"):
        g = g.reset_index(drop=True)
        if len(g) < 2:
            continue
        sim = cosine_similarity(TfidfVectorizer(stop_words="english").fit_transform(g.Requirement))
        for i, j in combinations(range(len(g)), 2):
            a, b, s = g.loc[i], g.loc[j], sim[i][j]
            ta, tb = a.Requirement.lower(), b.Requirement.lower()
            high = "High" in (a.Priority, b.Priority)
            ctype = None
            if any((x in ta and y in tb) or (y in ta and x in tb) for x, y in OPPOSITES):
                ctype, sev = "Contradiction", "High" if high else "Medium"
            else:
                na, nb = _numbers(a.Requirement), _numbers(b.Requirement)
                if s > 0.3 and any(u in nb and na[u] != nb[u] for u in na):
                    ctype, sev = "Numeric inconsistency", "High" if high else "Medium"
                elif s >= 0.6:
                    ctype, sev = "Duplicate / Overlap", "Low"
            if ctype:
                out.append({"Website": site, "Req_1": a.Req_ID, "Req_2": b.Req_ID, "Conflict_Type": ctype,
                            "Severity": sev, "Similarity": round(float(s), 2),
                            "Text_1": a.Requirement, "Text_2": b.Requirement})
    return pd.DataFrame(out, columns=["Website", "Req_1", "Req_2", "Conflict_Type", "Severity", "Similarity", "Text_1", "Text_2"])
