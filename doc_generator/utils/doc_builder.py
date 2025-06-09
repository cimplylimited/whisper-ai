from utils.logger import get_logger
from utils.auth import get_gdoc_service, get_drive_service
from utils.bullet_utils import build_bullet_requests
from utils.table_utils import build_table_requests

logger = get_logger(__name__)


def render_outline_sectioned_bullets(outline):
    """Renders canonical outline [{section, bullets}] to readable string."""
    lines = []
    for obj in outline:
        section = obj.get("section", "General")
        lines.append(section)
        for bullet in obj.get("bullets", []):
            lines.append(f"    • {bullet}")
    return "\n".join(lines).strip()


def render_key_takeaways_bullets(key_takeaways):
    """Render meta-bullets as readable bullets (optionally include metadata)."""
    lines = []
    for kt in key_takeaways:
        text = kt.get("text", "").strip()
        meta = " | ".join(str(kt.get(field, "")) for field in ["category", "type", "owner"] if kt.get(field))
        line = f"• {text}"
        if meta:
            line += f" [{meta} | Priority: {kt.get('priority_score', '')}]"
        lines.append(line)
    return "\n".join(lines).strip()


class DocBuilder:
    def __init__(self, template_doc_id, output_folder_id, admin_email, mapping, log_level="INFO"):
        self.template_doc_id = template_doc_id
        self.output_folder_id = output_folder_id
        self.admin_email = admin_email
        self.mapping = mapping
        self.log_level = log_level

        self.docs_service = get_gdoc_service()
        self.drive_service = get_drive_service()

    def generate_document(self, canonical_data):
        doc_id = None
        try:
            doc_id = self._copy_template()
            requests = []

            # ------------ SECTION PROCESSING -----------
            for section in self.mapping.get('sections', []):
                key = section['jsonKey']
                placeholder = section['docHeading']

                # Title, Date, Attendees (always text)
                if key == "title":
                    value = str(canonical_data.get("title", "No Title"))
                    requests += self._replace_text(placeholder, value)
                elif key == "date":
                    value = str(canonical_data.get("date", "No Date"))
                    requests += self._replace_text(placeholder, value)
                elif key == "attendees":
                    value = canonical_data.get("attendees", [])
                    attendee_text = ", ".join(value) if isinstance(value, list) else str(value)
                    requests += self._replace_text(placeholder, attendee_text)

                # Executive Summary (paragraph string)
                elif key == "summary":
                    summary = canonical_data.get("summary", "No Executive Summary or meeting details available.").strip()
                    requests += self._replace_text(placeholder, summary)

                # Outline: sectioned bullets
                elif key == "outline":
                    outline = canonical_data.get("outline", [])
                    outline_text = render_outline_sectioned_bullets(outline)
                    requests += self._replace_text(placeholder, outline_text)

                # Key Takeaways as meta-rich or simple bullets
                elif key == "key_takeaways":
                    ktake = canonical_data.get("key_takeaways", [])
                    takeaways_text = render_key_takeaways_bullets(ktake)
                    requests += self._replace_text(placeholder, takeaways_text)

            # ------------ TABLES -----------
            for table_map in self.mapping.get('tables', []):
                table_data = canonical_data.get(table_map['jsonKey'], [])
                if not table_data:
                    table_data = [table_map.get("default_row", ["No Updates"])]
                requests += build_table_requests(self.docs_service, doc_id, table_map, table_data)

            # ------------ LINKS -----------
            for link in self.mapping.get("links", []):
                val = canonical_data.get(link['jsonKey'], link.get('default', "No Updates"))
                requests += self._replace_text(link['placeholder'], val)

            # ------------ APPLY BATCH UPDATE -----------
            self.docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()

            self._move_to_output_folder(doc_id)
            doc_url = f"https://docs.google.com/document/d/{doc_id}"
            logger.info("Successfully generated doc: %s", doc_url)
            return {"success": True, "doc_id": doc_id, "doc_url": doc_url}
        except Exception as e:
            logger.error("Doc generation failed: %s", str(e))
            return {"success": False, "error": str(e)}

    def _copy_template(self):
        try:
            copied = self.drive_service.files().copy(
                fileId=self.template_doc_id,
                body={"name": "Automated Meeting Summary"},
                supportsAllDrives=True
            ).execute()
            doc_id = copied['id']
            logger.info("Template copied, new Doc ID: %s", doc_id)
            return doc_id
        except Exception as e:
            logger.error("Template copy failed: %s", str(e))
            raise

    def _move_to_output_folder(self, doc_id):
        try:
            file = self.drive_service.files().get(
                fileId=doc_id, fields='parents', supportsAllDrives=True
            ).execute()
            prev_parents = ",".join(file.get('parents', []))
            self.drive_service.files().update(
                fileId=doc_id,
                addParents=self.output_folder_id,
                removeParents=prev_parents,
                fields='id, parents',
                supportsAllDrives=True
            ).execute()
            logger.info("Moved doc %s to folder %s", doc_id, self.output_folder_id)
        except Exception as e:
            logger.error("Failed to move doc to folder: %s", str(e))
            raise

    def _replace_text(self, placeholder, text):
        return [{
            "replaceAllText": {
                "containsText": {"text": placeholder, "matchCase": True},
                "replaceText": text
            }
        }]