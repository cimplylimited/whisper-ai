from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULTS = {
    "title": "No Updates",
    "date": "No Updates",
    "attendees": ["No Updates"],
    "summary": "No Updates",
    "outline": ["No Updates"],
    "key_takeaways": ["No Updates"],
    "next_steps": [],
    "strategic_initiatives": [],
    "executive_followup": [],
    "james_grant_actions": [],
    "transcript_link": "No Updates",
    "summary_link": "No Updates",
}

TABLE_FIELDS = {
    "next_steps": [
        "description", "owner", "due_date", "priority_score", "urgency_score", "citation", "high_level_topic"
    ],
    "strategic_initiatives": [
        "description", "owner", "due_date", "priority_score", "urgency_score", "citation", "high_level_topic"
    ],
    "executive_followup": [
        "description", "owner", "due_date", "priority_score", "urgency_score", "citation", "high_level_topic"
    ],
    "james_grant_actions": [
        "description", "owner", "due_date", "priority_score", "urgency_score", "citation", "high_level_topic", "james_grant_reference"
    ],
}

TABLE_FIELD_DEFAULT = "N/A"

def ensure_list(val, default):
    if isinstance(val, list) and val:
        return val
    elif isinstance(val, str) and val.strip():
        return [val.strip()]
    else:
        return default.copy()

def normalize_summary(summary):
    if summary is None:
        return DEFAULTS["summary"]
    if isinstance(summary, list):
        summary = [str(x).strip() for x in summary if x and str(x).strip()]
        return "\n\n".join(summary) if summary else DEFAULTS["summary"]
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    return DEFAULTS["summary"]

def normalize_table(records, table_name):
    """
    Ensure each entry in a table section is a dict with all required fields.
    """
    fields = TABLE_FIELDS[table_name]
    if not (isinstance(records, list) and records):
        return []  # handled by docbuilder as 'No Updates'

    normed = []
    for i, record in enumerate(records):
        rec = {}
        # Defensive: sometimes tables are not list-of-dict (e.g. string or None)
        if not isinstance(record, dict):
            logger.warning(f"{table_name}: Entry {i} is not a dict ({type(record)}), got '{record}', auto-defaulting all fields.")
            for f in fields:
                rec[f] = TABLE_FIELD_DEFAULT
        else:
            for f in fields:
                rec[f] = record.get(f, TABLE_FIELD_DEFAULT)
                # If the value is empty string or None, default it
                if rec[f] in [None, ""]:
                    rec[f] = TABLE_FIELD_DEFAULT
        normed.append(rec)
    return normed

def normalize_transcript(raw_json):
    """
    Converts raw LLM transcript JSON into canonical, type-safe, mapping-ready format.
    All fields present, all types safe, all table entries padded with defaults.
    """
    d = {}

    # Scalars/fields
    d["title"] = str(raw_json.get("title") or DEFAULTS["title"])
    d["date"] = str(raw_json.get("date") or DEFAULTS["date"])

    raw_attendees = raw_json.get("attendees")
    # Coerce to list of str; filter blanks
    if isinstance(raw_attendees, list) and raw_attendees:
        attendees = [str(a).strip() for a in raw_attendees if a and str(a).strip()]
        d["attendees"] = attendees if attendees else DEFAULTS["attendees"]
    elif isinstance(raw_attendees, str) and raw_attendees.strip():
        d["attendees"] = [raw_attendees.strip()]
    else:
        d["attendees"] = DEFAULTS["attendees"]

    # Summary block
    d["summary"] = normalize_summary(raw_json.get("summary"))

    # Bullets fields
    for key in ["outline", "key_takeaways"]:
        raw = raw_json.get(key)
        d[key] = ensure_list(raw, DEFAULTS[key])

    # Table sections
    for tkey in ["next_steps", "strategic_initiatives", "executive_followup", "james_grant_actions"]:
        d[tkey] = normalize_table(raw_json.get(tkey), tkey)

    # Optional links
    for lk in ["transcript_link", "summary_link"]:
        v = raw_json.get(lk, DEFAULTS[lk])
        d[lk] = v if (v and isinstance(v, str)) else DEFAULTS[lk]

    # Could add: log keys in raw_json not in canonical schema (future debugging/auditing)
    return d

# Optional: Test with "bad" data
if __name__ == "__main__":
    example = {
        "title": "Test",
        "attendees": "John Doe",
        "summary": ["Item one", "", None, "Item two"],
        "outline": "Just this line",
        "next_steps": [
            {"description": "Do it!", "owner": "", "due_date": None, "priority_score": 8},
            "Not a dict"
        ]
    }
    import pprint
    pprint.pprint(normalize_transcript(example))