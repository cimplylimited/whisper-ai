from utils.logger import get_logger
import re
import datetime

logger = get_logger(__name__)

DEFAULTS = {
    "title": "No Updates",
    "date": datetime.date.today().isoformat(),
    "attendees": [],
    "summary": "No Executive Summary or meeting details available.",
    "outline": [{"section": "General", "bullets": ["No outline available."]}],
    "key_takeaways": [],
    "next_steps": [],
    "strategic_initiatives": [],
    "executive_followup": [],
    "james_grant_actions": [],
    "transcript_link": "No Updates",
    "summary_link": "No Updates",
}

ACTION_FIELDS = [
    "description", "owner", "due_date", "urgency_score",
    "priority_score", "citation", "high_level_topic"
]

def ensure_attendees(val):
    # List of non-empty, unique strings
    if isinstance(val, list):
        return [str(x).strip() for x in val if x and str(x).strip()]
    elif isinstance(val, str) and val.strip():
        return [val.strip()]
    return []

def normalize_summary(summary):
    # Always output a single string
    if isinstance(summary, str):
        return summary.strip()
    if isinstance(summary, (list, tuple)):
        return " ".join(str(s).strip() for s in summary if s and str(s).strip())
    return DEFAULTS["summary"]

def normalize_outline(outline):
    # Canonical structure: array of {"section", "bullets"}
    if isinstance(outline, list) and all(isinstance(x, dict) for x in outline):
        output = []
        for item in outline:
            section = item.get("section") or "General"
            bullets = item.get("bullets") or []
            output.append({"section": str(section), "bullets": [str(b) for b in bullets if b]})
        return output or DEFAULTS["outline"]
    # Handle legacy: flat or heading/detail pairs
    if isinstance(outline, list):
        items = [str(x) for x in outline if x]
        if len(items) % 2 == 0:
            return [
                {"section": items[i], "bullets": [items[i+1]]}
                for i in range(0, len(items), 2)
            ]
        return [{"section": "General", "bullets": items or ["No outline available."]}]
    return DEFAULTS["outline"]

def normalize_key_takeaways(kt):
    # Array of objects with strict schema for downstream analytics
    out = []
    required = ["text", "category", "type", "owner", "priority_score", "citation"]
    if not isinstance(kt, list): return []
    for item in kt:
        if isinstance(item, dict):
            obj = {k: item.get(k, "") for k in required}
            # Defensive type for score
            try: obj["priority_score"] = int(obj["priority_score"])
            except Exception: obj["priority_score"] = 1
            out.append(obj)
        elif isinstance(item, str):
            out.append(dict.fromkeys(required, ""))
            out[-1]["text"] = item
            out[-1]["priority_score"] = 1
    return out

def normalize_table(records, table_type):
    required = ACTION_FIELDS.copy()
    if table_type == "james_grant_actions":
        required.append("james_grant_reference")
    out = []
    for i, row in enumerate(records or []):
        rec = {}
        if not isinstance(row, dict):
            logger.warning(f"{table_type} row {i} is not dict; defaulting all fields.")
            rec = {k: "N/A" for k in required}
            if "james_grant_reference" in rec: rec["james_grant_reference"] = False
        else:
            for k in required:
                v = row.get(k)
                if k in ("urgency_score", "priority_score"):
                    try: v = int(v)
                    except Exception: v = 1
                if k == "james_grant_reference":
                    v = bool(v)
                rec[k] = v if v is not None else ("N/A" if k != "james_grant_reference" else False)
        out.append(rec)
    return out

def normalize_transcript(raw_json):
    d = {}
    d["title"] = str(raw_json.get("title") or DEFAULTS["title"]).strip()
    d["date"] = str(raw_json.get("date") or DEFAULTS["date"]).strip()
    d["attendees"] = ensure_attendees(raw_json.get("attendees"))
    d["summary"] = normalize_summary(raw_json.get("summary"))
    d["outline"] = normalize_outline(raw_json.get("outline"))
    d["key_takeaways"] = normalize_key_takeaways(raw_json.get("key_takeaways"))
    for t in ["next_steps", "strategic_initiatives", "executive_followup", "james_grant_actions"]:
        d[t] = normalize_table(raw_json.get(t), t)
    for lk in ["transcript_link", "summary_link"]:
        v = raw_json.get(lk, DEFAULTS[lk])
        d[lk] = v if isinstance(v, str) and v else DEFAULTS[lk]
    return d

if __name__ == "__main__":
    # Example with intended final structure
    example = {
        "title": "Product Strategy Q2 Alignment",
        "date": "2025-05-20",
        "attendees": ["Alice", "Bob"],
        "summary": "Major roadmap prioritization and post-mortem. Focus on SSO, API speed. Two critical risks flagged.",
        "outline": [
            {"section": "Product Roadmap", "bullets": ["SSO scheduled for June.", "API latency improvements in Q2."]},
            {"section": "Retrospective", "bullets": ["Past failed launches reviewed.", "Customer response analyzed."]}
        ],
        "key_takeaways": [
            {
                "text": "SSO required for major Q3 customer.",
                "category": "Product",
                "type": "Decision",
                "owner": "Team Lead",
                "priority_score": 10,
                "citation": "Para 8"
            }
        ],
        "next_steps": [
            {
                "description": "Migrate login system.",
                "owner": "Bob",
                "due_date": "2025-06-29",
                "urgency_score": 9,
                "priority_score": 9,
                "citation": "Para 10",
                "high_level_topic": "Engineering"
            }
        ],
        "james_grant_actions": []
    }
    import pprint
    pprint.pprint(normalize_transcript(example))