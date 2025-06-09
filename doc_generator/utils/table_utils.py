# utils/table_utils.py
from __future__ import annotations

from typing import List, Dict, Any, Sequence
from utils.logger import get_logger

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────────── #
# generic helpers                                                            #
# ────────────────────────────────────────────────────────────────────────── #
def _col_key(name: str) -> str:
    """Normalise a visible column name → canonical snake_key."""
    return name.lower().replace(" ", "_")


def _parse_columns(raw_cols: List[Any]) -> List[Dict[str, str]]:
    """
    Accept both
        • "Owner"
        • { header: Owner, field: owner }
    and return a list of dicts with keys header + field.
    """
    parsed: List[Dict[str, str]] = []
    for c in raw_cols:
        if isinstance(c, str):
            parsed.append({"header": c, "field": _col_key(c)})
        elif isinstance(c, dict) and {"header", "field"} <= set(c):
            parsed.append({"header": c["header"], "field": c["field"]})
        else:
            raise ValueError(f"Invalid column specification: {c}")
    return parsed


def _list_to_dict(seq: Sequence[str], field_names: List[str]) -> Dict[str, str]:
    """['a','b'] → {'field0': 'a', 'field1': 'b', …}"""
    return {field_names[i]: (seq[i] if i < len(seq) else "") for i in range(len(field_names))}


def _normalise_rows(rows: List[Any], field_names: List[str]) -> List[Dict[str, str]]:
    """
    Ensure every row ends up as a dict keyed by *field* names.
    """
    norm: List[Dict[str, str]] = []
    for r in rows:
        if isinstance(r, dict):
            norm.append(r)
        elif isinstance(r, (list, tuple)):
            norm.append(_list_to_dict(r, field_names))
        else:
            norm.append(_list_to_dict([str(r)], field_names))
    return norm


# ────────────────────────────────────────────────────────────────────────── #
# document position helpers                                                  #
# ────────────────────────────────────────────────────────────────────────── #
def _find_placeholder(doc: Dict[str, Any], ph: str) -> tuple[int, int]:
    """Return (start, end) indices of the first placeholder occurrence."""
    for el in doc.get("body", {}).get("content", []):
        if "paragraph" not in el:
            continue
        for run in el["paragraph"].get("elements", []):
            txt = run.get("textRun", {}).get("content", "")
            pos = txt.find(ph)
            if pos != -1:
                start = run["startIndex"] + pos
                return start, start + len(ph)
    raise ValueError(f"Placeholder '{ph}' not found in document")


def _find_table(doc: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """
    Return the table whose range contains idx; if none, return the very first
    table that starts *after* idx (handles newline shift).
    """
    after: list[Dict[str, Any]] = []
    for el in doc.get("body", {}).get("content", []):
        if "table" not in el:
            continue
        start, end = el["startIndex"], el["endIndex"]
        if start <= idx < end:
            return el["table"]
        if start > idx:
            after.append(el)
    if after:
        after.sort(key=lambda e: e["startIndex"])
        return after[0]["table"]
    raise ValueError("Inserted table not found (index mismatch)")


# ────────────────────────────────────────────────────────────────────────── #
# main public helper                                                         #
# ────────────────────────────────────────────────────────────────────────── #
def build_table_requests(
    docs_service,
    doc_id: str,
    tbl_map: Dict[str, Any],
    data: List[Any],
) -> None:
    """
    Delete placeholder, insert a real Docs table and populate it.

    • Supports both simple column list and {header,field} objects.
    • Writes bottom-to-top & right-to-left to keep indexes valid.
    • Executes its own API calls; returns None.
    """
    placeholder = tbl_map.get("placeholder") or f"{{{{{tbl_map['bookmark']}}}}}"

    columns = _parse_columns(tbl_map["columns"])   # [{header,field}, …]
    field_names = [c["field"] for c in columns]

    if not data:
        data = [tbl_map.get("default_row", {})]
    rows = _normalise_rows(data, field_names)

    # ------------------------------------------------------------------ #
    # 1. remove placeholder & insert empty table                          #
    # ------------------------------------------------------------------ #
    doc = docs_service.documents().get(documentId=doc_id).execute()
    start, end = _find_placeholder(doc, placeholder)

    insert_empty_table = [
        {"deleteContentRange": {"range": {"startIndex": start, "endIndex": end}}},
        {
            "insertTable": {
                "rows": len(rows) + 1,          # + header
                "columns": len(columns),
                "location": {"index": start},
            }
        },
    ]
    docs_service.documents().batchUpdate(
        documentId=doc_id, body={"requests": insert_empty_table}
    ).execute()

    # ------------------------------------------------------------------ #
    # 2. locate table & prepare insertText requests                      #
    # ------------------------------------------------------------------ #
    doc = docs_service.documents().get(documentId=doc_id).execute()
    table = _find_table(doc, start)

    def _ins(text: str, idx: int) -> Dict[str, Any]:
        safe = text if text.strip() else " "        # NBSP avoids empty-string 400
        return {"insertText": {"location": {"index": idx}, "text": safe}}

    insert_reqs: List[Dict[str, Any]] = []

    total_rows = len(table["tableRows"])

    # bottom-to-top, right-to-left
    for r in range(total_rows - 1, -1, -1):
        cell_row = table["tableRows"][r]["tableCells"]
        for c in range(len(cell_row) - 1, -1, -1):
            cell = cell_row[c]
            idx_in_cell = cell["startIndex"] + 1

            if r == 0:  # header row
                value = columns[c]["header"]
            else:
                row_dict = rows[r - 1] if r - 1 < len(rows) else {}
                value = str(row_dict.get(columns[c]["field"], "")).strip()

            insert_reqs.append(_ins(value, idx_in_cell))

    if insert_reqs:
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": insert_reqs}
        ).execute()

    logger.info(
        "Rendered table for '%s' (%d×%d) in document %s",
        placeholder,
        len(rows) + 1,
        len(columns),
        doc_id,
    )