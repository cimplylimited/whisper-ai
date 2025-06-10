import logging
from utils.logger import get_logger

logger = get_logger(__name__)

def build_bullet_requests(items, insert_index):
    """
    Build Google Docs API requests to insert a real bulleted list at the given location.
    Returns a list of batchUpdate requests.
    """
    # Defensive: items must be a non-empty list
    if not items or not any(str(i).strip() for i in items):
        logger.warning("[BULLETS] No non-blank bullet items passed. Inserting 'No Updates'.")
        items = ["No Updates"]
    if isinstance(items, str):
        items = [items]

    requests = []
    start_index = insert_index
    curr_index = start_index
    for i, bullet in enumerate(items):
        bullet_str = str(bullet).strip()
        if not bullet_str:
            continue
        logger.info(f"[BULLETS] Bullet {i}: '{bullet_str}' at {curr_index}")
        requests.append({
            'insertText': {
                'location': {'index': curr_index},
                'text': bullet_str + '\n'
            }
        })
        curr_index += len(bullet_str) + 1

    # Bulletize inserted range
    if curr_index > start_index:
        logger.info(f"[BULLETS] Applying bullet paragraph style: {start_index}-{curr_index}")
        requests.append({
            "createParagraphBullets": {
                "range": {
                    "startIndex": start_index,
                    "endIndex": curr_index
                },
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })
    logger.info(f"[BULLETS] Finished bullets. End index: {curr_index}")
    return requests

def build_outline_section_requests(outline_sections, insert_index):
    """
    Build requests to insert outline sections, each with a Heading 3 and real bullets, at insert_index.
    outline_sections: [{'section': str, 'bullets': [str,...]}, ...]
    Returns a list of batchUpdate requests.
    """
    requests = []
    curr_index = insert_index

    # Optional: hard break before first heading
    logger.info(f"[OUTLINE] Inserting forced paragraph break '\\n' at index={curr_index}")
    requests.append({
        "insertText": {
            "location": {"index": curr_index},
            "text": "\n"
        }
    })
    curr_index += 1

    for s_num, section in enumerate(outline_sections):
        section_title = section.get('section', '').strip()
        bullets = section.get('bullets', []) or []

        # Insert heading
        if section_title:
            logger.info(f"[OUTLINE] Section {s_num}: Inserting H3 '{section_title}' at {curr_index}")
            requests.append({
                "insertText": {
                    "location": {"index": curr_index},
                    "text": section_title + "\n"
                }
            })
            requests.append({
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": curr_index,
                        "endIndex": curr_index + len(section_title)
                    },
                    "paragraphStyle": {"namedStyleType": "HEADING_3"},
                    "fields": "namedStyleType"
                }
            })
            curr_index += len(section_title) + 1

        # Insert bullets for this section
        bullets_start = curr_index
        for b_num, bullet in enumerate(bullets):
            text = bullet.strip()
            if not text:
                continue
            logger.info(f"[OUTLINE]   Bullet {b_num}: Inserting at {curr_index}: '{text}'")
            requests.append({
                "insertText": {
                    "location": {"index": curr_index},
                    "text": text + "\n"
                }
            })
            curr_index += len(text) + 1
        bullets_end = curr_index
        if bullets_end > bullets_start:
            requests.append({
                "createParagraphBullets": {
                    "range": {
                        "startIndex": bullets_start,
                        "endIndex": bullets_end
                    },
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                }
            })

        # Optional: Blank line after each section
        requests.append({
            "insertText": {
                "location": {"index": curr_index},
                "text": "\n"
            }
        })
        curr_index += 1

    logger.info(f"[OUTLINE] Finished outline batch, ending at {curr_index}")
    return requests

def flatten_outline_for_bullets(outline_sections):
    """
    Fallback: Flatten outline for a plain newline-joined bullet list.
    """
    lines = []
    for section in outline_sections:
        section_title = section.get('section', '').strip()
        bullets = section.get('bullets', []) or []
        if section_title:
            lines.append(section_title)
        for bullet in bullets:
            lines.append(f"    {bullet}")
    return lines

# For marker-based workflows, you do NOT want to manage batch update or content deletion in here.
# Instead, do that in your DocBuilder or a dedicated doc_utils.py as previously discussed.