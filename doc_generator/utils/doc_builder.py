from typing import List, Dict, Any
import pprint

from utils.logger import get_logger
from utils.auth import get_gdoc_service, get_drive_service
from utils.doc_utils import (
    find_marker_index,
    delete_marker,
    marker_exists,
)
from utils.bullet_utils import (
    build_bullet_requests,
    build_outline_section_requests,
    flatten_outline_for_bullets,
)
from utils.table_utils import build_table_requests
from utils.key_takeaway_util import build_key_takeaway_requests

logger = get_logger(__name__)

RICH_INSERTS = {
    "<<OUTLINE_MARKER>>": {
        "json_key": "outline",
        "builder": build_outline_section_requests,
        "type": "outline",
    },
    "<<KEY_TAKEAWAYS_MARKER>>": {
        "json_key": "key_takeaways",
        "builder": build_key_takeaway_requests,
        "type": "key_takeaways",
    },
    # Extend for more rich insert sections if needed
}

class DocBuilder:
    def __init__(
        self,
        template_doc_id: str,
        output_folder_id: str,
        admin_email: str,
        mapping: Dict[str, Any],
        log_level: str = "INFO",
    ):
        self.template_doc_id = template_doc_id
        self.output_folder_id = output_folder_id
        self.admin_email = admin_email
        self.mapping = mapping

        logger.setLevel(log_level.upper())
        self.docs_service = get_gdoc_service()
        self.drive_service = get_drive_service()

    def generate_document(self, canonical: Dict[str, Any]) -> Dict[str, Any]:
        doc_id: str | None = None
        try:
            # 1. Dynamic output file name: "Meeting Summary | {TITLE}"
            title = canonical.get("title", "Untitled").strip() or "Untitled"
            filename = f"Meeting Summary | {title}"
            doc_id = self._copy_template(filename)

            # 2. Flat replacements (including marker drops for rich content)
            flat_reqs = self._flat_pass_requests(canonical)
            if flat_reqs:
                logger.info("Flat batchUpdate requests:\n%s", pprint.pformat(flat_reqs, indent=2))
                self.docs_service.documents().batchUpdate(
                    documentId=doc_id, body={"requests": flat_reqs}
                ).execute()

            # 3. Rich content replacement: process each marker
            for marker, cfg in RICH_INSERTS.items():
                json_key = cfg["json_key"]
                builder = cfg["builder"]
                item_type = cfg["type"]
                section_data = canonical.get(json_key, [])

                if marker_exists(self.docs_service, doc_id, marker):
                    idx = find_marker_index(self.docs_service, doc_id, marker)
                    # For key_taekaways, builder returns a ready requests list.
                    if item_type == "key_takeaways":
                        reqs = builder(
                            self.docs_service, doc_id,
                            placeholder_fragment=marker,
                            takeaways=section_data,
                        )
                        if reqs:
                            logger.info(f"[KEY_TAKEAWAYS] Inserting {len(reqs)} requests at marker {marker}")
                            self.docs_service.documents().batchUpdate(
                                documentId=doc_id, body={"requests": reqs}
                            ).execute()
                    else:
                        reqs = builder(section_data, idx)
                        if reqs:
                            logger.info(f"[RICH_INSERT] Inserting {len(reqs)} requests at marker {marker}, json_key={json_key}")
                            self.docs_service.documents().batchUpdate(
                                documentId=doc_id, body={"requests": reqs}
                            ).execute()
                        delete_marker(self.docs_service, doc_id, marker)

            # 4. Tables still use their own placeholder locate/delete/insert logic
            for tbl in self.mapping.get("tables", []):
                rows = canonical.get(tbl["jsonKey"], [])
                build_table_requests(self.docs_service, doc_id, tbl, rows)

            self._move_to_output_folder(doc_id)
            url = f"https://docs.google.com/document/d/{doc_id}"
            logger.info("Successfully generated doc: %s", url)
            return {"success": True, "doc_id": doc_id, "doc_url": url}

        except Exception as exc:
            logger.exception("Doc generation failed")
            return {"success": False, "doc_id": doc_id, "doc_url": None, "error": str(exc)}

    def _flat_pass_requests(self, data: Dict[str, Any]) -> list:
        """
        Returns list of replaceAllText requests, swapping out any rich section for a marker.
        """
        reqs: list[dict] = []
        rich_json_keys = {cfg["json_key"] for cfg in RICH_INSERTS.values()}

        for section in self.mapping.get("sections", []):
            ph    = section["docHeading"]
            jkey  = section["jsonKey"]
            stype = section["type"]
            raw   = data.get(jkey, section.get("default"))

            if jkey in rich_json_keys:
                for m, cfg in RICH_INSERTS.items():
                    if cfg["json_key"] == jkey:
                        marker = m
                        break
                reqs.append({
                    "replaceAllText": {
                        "containsText": {"text": ph, "matchCase": True},
                        "replaceText": marker
                    }
                })
                continue

            if stype in ("text", "block"):
                val = self._transform(raw, section)
                reqs.append({
                    "replaceAllText": {
                        "containsText": {"text": ph, "matchCase": True},
                        "replaceText": val
                    }
                })
            elif stype == "bullets":
                items = raw if isinstance(raw, list) else [raw]
                bullets_text = "\n".join(str(x) for x in items)
                reqs.append({
                    "replaceAllText": {
                        "containsText": {"text": ph, "matchCase": True},
                        "replaceText": bullets_text
                    }
                })

        for link in self.mapping.get("links", []):
            val = data.get(link["jsonKey"], link.get("default", ""))
            reqs.append({
                "replaceAllText": {
                    "containsText": {"text": link["placeholder"], "matchCase": True},
                    "replaceText": str(val)
                }
            })

        return reqs

    @staticmethod
    def _transform(val: Any, cfg: Dict[str, Any]) -> str:
        if cfg.get("transform") == "join_comma" and isinstance(val, list):
            val = ", ".join(map(str, val))
        if cfg.get("transform") == "iso-date" and isinstance(val, str):
            val = val[:10]
        if cfg.get("postprocess") == "join_paragraphs":
            val = "\n\n".join(map(str, val)) if isinstance(val, list) else str(val).strip()
        if val in (None, "", [], {}):
            val = cfg.get("default", "No Updates")
        return str(val)

    def _copy_template(self, file_title: str) -> str:
        return (
            self.drive_service.files()
            .copy(
                fileId=self.template_doc_id,
                body={"name": file_title},
                supportsAllDrives=True,
            )
            .execute()["id"]
        )

    def _move_to_output_folder(self, doc_id: str) -> None:
        parents = (
            self.drive_service.files()
            .get(fileId=doc_id, fields="parents", supportsAllDrives=True)
            .execute()
            .get("parents", [])
        )
        prev = ",".join(parents) if parents else None
        (
            self.drive_service.files()
            .update(
                fileId=doc_id,
                addParents=self.output_folder_id,
                removeParents=prev,
                fields="id, parents",
                supportsAllDrives=True,
            )
            .execute()
        )