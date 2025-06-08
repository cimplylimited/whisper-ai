from utils.logger import get_logger
from utils.auth import get_gdoc_service, get_drive_service
from utils.bullet_utils import build_bullet_requests
from utils.table_utils import build_table_requests

logger = get_logger(__name__)

from utils.logger import get_logger
from utils.auth import get_gdoc_service, get_drive_service
from utils.bullet_utils import build_bullet_requests
from utils.table_utils import build_table_requests

logger = get_logger(__name__)

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

            # Replace simple (text) placeholders
            for field in self.mapping['fields']:
                if field['type'] == 'text':
                    val = canonical_data.get(field['jsonKey'], field.get("default", "No Updates"))
                    val = self._apply_transform(val, field)
                    requests += self._replace_text(field['placeholder'], val)

            # Bullets
            for field in self.mapping['fields']:
                if field['type'] == 'bullets':
                    val = canonical_data.get(field['jsonKey'], field.get("default", ["No Updates"]))
                    items = val if isinstance(val, list) and val else ["No Updates"]
                    requests += build_bullet_requests(self.docs_service, doc_id, field['placeholder'], items)

            # Tables
            for table_map in self.mapping.get('tables', []):
                table_data = canonical_data.get(table_map['jsonKey'], [])
                requests += build_table_requests(self.docs_service, doc_id, table_map, table_data)

            # Links (optional)
            for link in self.mapping.get("links", []):
                val = canonical_data.get(link['jsonKey'], link.get('default', "No Updates"))
                requests += self._replace_text(link['placeholder'], val)

            # Batch API call to update doc
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
        # Copy template file; return new doc_id
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
            # You *must* use supportsAllDrives for shared folders/drives
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

    def _apply_transform(self, value, field):
        if field.get("transform") == "join(', ')":
            if isinstance(value, list):
                return ", ".join(str(x) for x in value if x)
        elif field.get("transform") == "iso-date":
            if isinstance(value, str) and len(value) >= 10:
                return value[:10]
        elif field.get("postprocess") == "join_paragraphs":
            if isinstance(value, list):
                return "\n\n".join(str(x) for x in value if x)
        return value