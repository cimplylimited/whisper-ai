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
    "subject", "description", "owner", "due_date",
    "urgency_score", "priority_score", "citation", "high_level_topic"
]

def ensure_attendees(val):
    if isinstance(val, list):
        return [str(x).strip() for x in val if x and str(x).strip()]
    elif isinstance(val, str) and val.strip():
        return [val.strip()]
    return []

def normalize_summary(summary):
    if isinstance(summary, str):
        return summary.strip()
    if isinstance(summary, list):
        return " ".join(str(s).strip() for s in summary if s and str(s).strip())
    return DEFAULTS["summary"]

def normalize_outline(outline):
    if isinstance(outline, list) and all(isinstance(x, dict) and "section" in x and "bullets" in x for x in outline):
        return [{"section": o.get("section") or "General", "bullets": [str(b) for b in (o.get("bullets") or []) if b]} for o in outline]
    if isinstance(outline, list):
        items = [str(x) for x in outline if x]
        return [{"section": "General", "bullets": items if items else ["No outline available."]}]
    return DEFAULTS["outline"]

def normalize_key_takeaways(kt):
    required = ["subject","text", "category", "type", "owner", "priority_score", "citation"]
    result = []
    if not kt or not isinstance(kt, list): return []
    for item in kt:
        if isinstance(item, dict):
            norm = {k: item.get(k, "") for k in required}
            try: norm["priority_score"] = int(norm.get("priority_score", 1))
            except Exception: norm["priority_score"] = 1
            result.append(norm)
        elif isinstance(item, str):
            result.append({"text": item, "category": "", "type": "", "owner": "", "priority_score": 1, "citation": ""})
    return result

def normalize_table(records, table_type):
    required = ACTION_FIELDS.copy()
    if table_type == "james_grant_actions":
        required.append("james_grant_reference")
    out = []
    for i, row in enumerate(records or []):
        if isinstance(row, dict):
            rec = {}
            for idx, key in enumerate(required):
                # description/subject coalescing for legacy support
                if key == "description" and not row.get("description") and row.get("subject"):
                    rec[key] = row.get("subject", "")
                elif key == "subject" and not row.get("subject") and row.get("description"):
                    rec[key] = row.get("description", "")
                else:
                    rec[key] = row.get(key, "N/A")
            for k in ["urgency_score", "priority_score"]:
                try: rec[k] = int(rec.get(k, 1))
                except Exception: rec[k] = 1
            rec["due_date"] = rec.get("due_date", "N/A") or "N/A"
            if table_type == "james_grant_actions":
                rec["james_grant_reference"] = bool(row.get("james_grant_reference", False))
            out.append(rec)
        elif isinstance(row, list):
            rec = {}
            for idx, key in enumerate(required):
                rec[key] = row[idx] if idx < len(row) else "N/A"
            for k in ["urgency_score", "priority_score"]:
                try: rec[k] = int(rec.get(k, 1))
                except Exception: rec[k] = 1
            if table_type == "james_grant_actions":
                rec["james_grant_reference"] = bool(rec.get("james_grant_reference", False))
            out.append(rec)
        else:
            logger.warning(f"{table_type}: Fallback/default row for type {type(row)}")
            rec = {k: "N/A" for k in required}
            if "james_grant_reference" in rec: rec["james_grant_reference"] = False
            out.append(rec)
    return out

def normalize_transcript(raw_json):
    d = {}
    d["title"] = str(raw_json.get("title", DEFAULTS["title"])).strip()
    d["date"] = str(raw_json.get("date", DEFAULTS["date"])).strip()
    d["attendees"] = ensure_attendees(raw_json.get("attendees"))
    d["summary"] = normalize_summary(raw_json.get("summary"))
    d["outline"] = normalize_outline(raw_json.get("outline"))
    d["key_takeaways"] = normalize_key_takeaways(raw_json.get("key_takeaways"))
    for t in ["next_steps", "strategic_initiatives", "executive_followup", "james_grant_actions"]:
        d[t] = normalize_table(raw_json.get(t), t)
    for lk in ["transcript_link", "summary_link"]:
        v = raw_json.get(lk, DEFAULTS[lk])
        d[lk] = v if (v and isinstance(v, str)) else DEFAULTS[lk]
    return d

if __name__ == "__main__":
    example = {
        "title": "Sample Meeting",
        "date": "2025-05-01",
        "attendees": ["Jane Roe", "John Smith", "James Grant"],
        "summary": "Quarterly planning. Risks discussed.",
        "outline": [{"section": "Q1 Review", "bullets": ["Achievement 1", "Issue X"]}],
        "key_takeaways": [{"text": "Risk flagged.", "category": "Vendor", "type": "Risk", "owner": "Smith", "priority_score": 7, "citation": "Para 5"}, "Early win!"],
        "next_steps": [
            ["Discuss API ;", "Jane", "2025-05-06", 8, 10, "Para 10", "Tech"],
            {"description": "Send plan", "owner": "John", "due_date": "2025-05-07", "urgency_score": 7, "priority_score": 8, "citation": "Para 13", "high_level_topic": "Strategy"}
        ],
        "james_grant_actions": []
    }
    import pprint
    pprint.pprint(normalize_transcript(example))