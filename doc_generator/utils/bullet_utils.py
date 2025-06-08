from utils.logger import get_logger

logger = get_logger(__name__)

def build_bullet_requests(docs_service, doc_id, placeholder, items):
    """
    Generate Google Docs API requests to replace placeholder in the document
    with a plain (unformatted) bulleted list (i.e., text with dashes).
    If items is empty, inserts '- No Updates'.
    """
    if not items or not any(str(i).strip() for i in items):
        logger.warning(f"No non-blank bullet items passed for placeholder '{placeholder}'. Inserting '- No Updates'.")
        items = ["No Updates"]
    text = '\n'.join(f"- {str(item)}" for item in items)
    return [{
        "replaceAllText": {
            "containsText": {"text": placeholder, "matchCase": True},
            "replaceText": text
        }
    }]