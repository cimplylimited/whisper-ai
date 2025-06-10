import logging
from utils.logger import get_logger

logger = get_logger(__name__)

def find_marker_index(service, doc_id, marker):
    """
    Finds the start index of a marker string (e.g. <<OUTLINE_MARKER>>) in the document.
    Returns the startIndex suitable for Google Docs API insertions.
    Raises RuntimeError if not found.
    """
    logger.info(f"[DOC_UTILS] Locating marker: {marker}")
    doc = service.documents().get(documentId=doc_id).execute()
    for el in doc.get("body", {}).get("content", []):
        para = el.get("paragraph", {})
        for seg in para.get("elements", []):
            text_run = seg.get("textRun", {})
            txt = text_run.get("content", "")
            if marker in txt:
                index = seg.get("startIndex", None)
                logger.info(f"[DOC_UTILS] Marker '{marker}' found at {index}")
                return index
    raise RuntimeError(f"Marker '{marker}' not found in doc")

def delete_marker(service, doc_id, marker):
    """
    Deletes all occurrences of the marker string in the document.
    (Usually called after rich insertion is complete.)
    """
    logger.info(f"[DOC_UTILS] Deleting marker '{marker}' from doc_id {doc_id}")
    requests = [{
        "replaceAllText": {
            "containsText": {"text": marker, "matchCase": True},
            "replaceText": ""
        }
    }]
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

def marker_exists(service, doc_id, marker):
    """
    Returns True if the marker exists anywhere in the doc, else False.
    """
    logger.info(f"[DOC_UTILS] Checking for marker '{marker}' existence in doc_id {doc_id}")
    doc = service.documents().get(documentId=doc_id).execute()
    for el in doc.get("body", {}).get("content", []):
        para = el.get("paragraph", {})
        for seg in para.get("elements", []):
            text_run = seg.get("textRun", {})
            txt = text_run.get("content", "")
            if marker in txt:
                logger.info(f"[DOC_UTILS] Marker '{marker}' FOUND in doc_id {doc_id}")
                return True
    logger.info(f"[DOC_UTILS] Marker '{marker}' NOT found in doc_id {doc_id}")
    return False

def get_all_markers(service, doc_id, markers=None):
    """
    Scans doc and returns a set of found marker strings.
    If `markers` (list/set) provided, only reports those; otherwise, returns all <<ALL_CAPS_MARKERS>> found.
    """
    found = set()
    doc = service.documents().get(documentId=doc_id).execute()
    for el in doc.get("body", {}).get("content", []):
        para = el.get("paragraph", {})
        for seg in para.get("elements", []):
            text_run = seg.get("textRun", {})
            txt = text_run.get("content", "")
            if not txt:
                continue
            if markers:
                for marker in markers:
                    if marker in txt:
                        found.add(marker)
            else:
                # naive marker detection: detects <<...>>
                import re
                found.update(re.findall(r'<<[A-Z0-9_-]+>>', txt))
    return found

# General utility; can extend with more doc-manipulation functions as needed.