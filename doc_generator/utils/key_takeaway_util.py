from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

def build_key_takeaway_requests(
    docs_service,
    doc_id: str,
    placeholder_fragment: str = "KEY_TAKEAWAYS",
    takeaways: List[Dict[str, Any]] | None = None,
) -> List[Dict]:
    """
    • Delete the paragraph that contains the fragment 'KEY_TAKEAWAYS'
      (works even when '{{', '}}' are separate runs).
    • Insert blocks:
          HEADING_3  subject
          HEADING_5  Category | Type | Owner | Priority | Citation
          P          free text
    Returns a batch-ready list of requests.
    """
    takeaways = takeaways or [{"subject": "No Updates", "text": ""}]

    doc = docs_service.documents().get(documentId=doc_id).execute()
    start, end = _paragraph_bounds_with_fragment(doc, placeholder_fragment)

    reqs: list[dict] = [
        {"deleteContentRange": {"range": {"startIndex": start, "endIndex": end}}}
    ]
    idx = start

    def _insert(text: str) -> int:
        nonlocal idx
        reqs.append({"insertText": {"location": {"index": idx}, "text": text}})
        idx += len(text)
        return len(text)

    def _style(style: str, length: int):
        reqs.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": idx - length, "endIndex": idx},
                    "paragraphStyle": {"namedStyleType": style},
                    "fields": "namedStyleType",
                }
            }
        )

    for kt in takeaways:
        subj = (kt.get("subject") or kt.get("text", "")[:60]).strip()
        body = kt.get("text", "").strip()

        meta = " | ".join(
            f"{label}: {kt[fld]}"
            for fld, label in (
                ("category", "Category"),
                ("type",     "Type"),
                ("owner",    "Owner"),
                ("priority_score", "Priority"),
                ("citation", "Citation"),
            )
            if kt.get(fld)
        )

        # Subject  (HEADING_3)
        _style("HEADING_3", _insert(subj + "\n"))

        # Meta line (HEADING_5)
        if meta:
            _style("HEADING_5", _insert(meta + "\n"))

        # Body text (NORMAL_TEXT)
        if body:
            length = _insert(body + "\n\n")        # add two newlines after body
            _style("NORMAL_TEXT", length)          # reset to normal paragraph

    logger.debug("KT-requests built: %d", len(reqs))
    return reqs


def _paragraph_bounds_with_fragment(doc: Dict[str, Any], frag: str) -> tuple[int, int]:
    for el in doc.get("body", {}).get("content", []):
        para = el.get("paragraph")
        if not para:
            continue
        full = "".join(run.get("textRun", {}).get("content", "") for run in para["elements"])
        if frag in full:
            return para["elements"][0]["startIndex"], el["endIndex"]
    raise ValueError(f"Paragraph containing '{frag}' not found")