# utils/doc_builder.py
from __future__ import annotations
from typing import List, Dict, Any

from utils.logger import get_logger
from utils.auth import get_gdoc_service, get_drive_service
from utils.bullet_utils import build_bullet_requests
from utils.table_utils import build_table_requests
from utils.key_takeaway_util import build_key_takeaway_requests

logger = get_logger(__name__)


class DocBuilder:
    # ──────────────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────────
    def generate_document(self, canonical: Dict[str, Any]) -> Dict[str, Any]:
        doc_id: str | None = None
        try:
            doc_id = self._copy_template()

            simple_reqs, kt_items = self._first_pass_requests(doc_id, canonical)
            if simple_reqs:
                self.docs_service.documents().batchUpdate(
                    documentId=doc_id, body={"requests": simple_reqs}
                ).execute()

            # second pass – only if we captured items
            if kt_items:
                kt_reqs = build_key_takeaway_requests(
                    self.docs_service, doc_id, "KEY_TAKEAWAYS", kt_items
                )
                if kt_reqs:
                    self.docs_service.documents().batchUpdate(
                        documentId=doc_id, body={"requests": kt_reqs}
                    ).execute()

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

    # ──────────────────────────────────────────────────────────────
    def _first_pass_requests(
        self, doc_id: str, data: Dict[str, Any]
    ) -> tuple[List[Dict], list | None]:
        reqs: List[Dict] = []
        kt_items: list | None = None

        for section in self.mapping.get("sections", []):
            ph, jkey, stype = section["docHeading"], section["jsonKey"], section["type"]
            raw = data.get(jkey, section.get("default"))

            if stype in ("text", "block"):
                reqs += self._replace_text(ph, self._transform(raw, section))

            elif stype == "bullets":
                items = raw if isinstance(raw, list) else [raw]

                if jkey == "key_takeaways" and kt_items is None:
                    kt_items = items         # FIX: do NOT delete placeholder here
                else:
                    reqs += self._replace_text(ph, "")      # normal bullet sections
                    reqs += build_bullet_requests(self.docs_service, doc_id, ph, items)

        for link in self.mapping.get("links", []):
            val = data.get(link["jsonKey"], link.get("default", ""))
            reqs += self._replace_text(link["placeholder"], str(val))

        return reqs, kt_items

    # ──────────────────────────────────────────────────────────────
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

    def _copy_template(self) -> str:
        return self.drive_service.files().copy(
            fileId=self.template_doc_id,
            body={"name": "Automated Meeting Summary"},
            supportsAllDrives=True,
        ).execute()["id"]

    def _move_to_output_folder(self, doc_id: str) -> None:
        parents = self.drive_service.files().get(
            fileId=doc_id, fields="parents", supportsAllDrives=True
        ).execute().get("parents", [])
        prev = ",".join(parents) if parents else None
        self.drive_service.files().update(
            fileId=doc_id,
            addParents=self.output_folder_id,
            removeParents=prev,
            fields="id, parents",
            supportsAllDrives=True,
        ).execute()

    @staticmethod
    def _replace_text(ph: str, txt: str) -> List[Dict]:
        return [{"replaceAllText": {"containsText": {"text": ph, "matchCase": True}, "replaceText": txt}}]