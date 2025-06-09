from utils.logger import get_logger

logger = get_logger(__name__)

def build_bullet_requests(docs_service, doc_id, placeholder, items):
    """
    Generate Google Docs API requests to replace the placeholder in the Google Doc
    with a plaintext bulleted list (each line prefixed with `- `).
    If items is empty or only blank, inserts '- No Updates'.
    """
    # Ensure items is a non-empty list of strings
    if not items or not any(str(i).strip() for i in items):
        logger.warning(f"No non-blank bullet items passed for placeholder '{placeholder}'. Inserting '- No Updates'.")
        items = ["No Updates"]

    # If items accidentally passed as a string, convert to single-item list
    if isinstance(items, str):
        items = [items]

    text = '\n'.join(f"- {str(item)}" for item in items)
    logger.info(f"Rendering bullets for '{placeholder}' with {len(items)} items.")

    return [{
        "replaceAllText": {
            "containsText": {"text": placeholder, "matchCase": True},
            "replaceText": text
        }
    }]