from utils.logger import get_logger

logger = get_logger(__name__)

def build_table_requests(docs_service, doc_id, table_map, table_data):
    """
    For MVP: replace the bookmark placeholder text with a plain-text table (markdown style)
    If table_data is empty, insert a row with 'No Updates'.
    """
    bookmark = table_map.get("bookmark")
    columns = table_map.get("columns", [])

    def as_markdown_table(headers, rows):
        col_line = " | ".join(headers)
        divider  = " | ".join(['---'] * len(headers))
        row_lines = []
        for row in rows:
            # If row is a dict, extract values in the right order:
            if isinstance(row, dict):
                ordered = [str(row.get(col.lower().replace(" ", "_"), "N/A")) for col in headers]
            else:
                logger.warning(f"Non-dict row in table {bookmark}: {row}. Falling back to string values.")
                ordered = [str(cell) for cell in row]
            row_lines.append(" | ".join(ordered))
        return "\n".join([col_line, divider] + row_lines)

    if table_data and len(table_data) > 0:
        rows = []
        for entry in table_data:
            if isinstance(entry, dict):
                row = [entry.get(col.lower().replace(" ", "_"), "N/A") for col in columns]
            else:
                logger.warning(f"Non-dict entry in table {bookmark}: {entry}. Falling back to all-string row.")
                row = [str(entry) for col in columns]
            rows.append(row)
    else:
        logger.info(f"No data for table '{bookmark}', inserting 'No Updates' row.")
        row = ["No Updates"] + ["N/A"] * (len(columns) - 1)
        rows = [row]

    markdown_table = as_markdown_table(columns, rows)

    # Replace the placeholder (or bookmark text) in the doc:
    return [{
        "replaceAllText": {
            "containsText": {"text": f"{{{{{bookmark}}}}}", "matchCase": True},
            "replaceText": markdown_table
        }
    }]