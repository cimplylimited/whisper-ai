import os
import json
from pathlib import Path
from dotenv import load_dotenv
import yaml

from utils.logger import get_logger

logger = get_logger(__name__)

# Load .env from parent dir
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from utils.schema import normalize_transcript
from utils.doc_builder import DocBuilder

def load_mapping(mapping_path):
    try:
        with open(mapping_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load mapping.yaml: {e}")
        raise

def load_transcript(transcript_path):
    try:
        with open(transcript_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load transcript JSON: {e}")
        raise

def main(transcript_json_path):
    logger.info(f"Loading transcript: {transcript_json_path}")
    raw_transcript = load_transcript(transcript_json_path)

    # Normalize
    normalized = normalize_transcript(raw_transcript)
    logger.info("Transcript normalized.")

    # Load mapping
    mapping_path = os.getenv("DOCGEN_MAPPING_YAML_PATH")
    if not mapping_path:
        logger.error("DOCGEN_MAPPING_YAML_PATH not set in .env")
        exit(1)
    mapping = load_mapping(mapping_path)
    logger.info("Mapping loaded.")

    # Doc config from env
    template_doc_id = os.getenv("DOCGEN_TEMPLATE_DOC_ID")
    output_folder_id = os.getenv("DOCGEN_OUTPUT_FOLDER_ID")
    admin_email = os.getenv("DOCGEN_ADMIN_EMAIL")

    # Validate required env
    for var, val in [
        ("DOCGEN_TEMPLATE_DOC_ID", template_doc_id),
        ("DOCGEN_OUTPUT_FOLDER_ID", output_folder_id),
        ("DOCGEN_ADMIN_EMAIL", admin_email),
    ]:
        if not val:
            logger.error(f"{var} not set in .env")
            exit(1)

    logger.info(f"Using template_doc_id: {template_doc_id}")

    import pprint
    pprint.pp(normalized.get("key_takeaways", [])[:2])  # Inspect first 2 KT

    # Initialize and run DocBuilder
    doc_builder = DocBuilder(
        template_doc_id=template_doc_id,
        output_folder_id=output_folder_id,
        admin_email=admin_email,
        mapping=mapping,
    )
    logger.info("DocBuilder initialized.")

    try:
        result = doc_builder.generate_document(normalized)
    except Exception as e:
        logger.error(f"Error during doc generation: {e}", exc_info=True)
        print("Failed to generate doc. See logs for details.")
        exit(1)

    if result.get("success"):
        print(f"Successfully generated doc: {result['doc_url']}")
        logger.info(f"Output Doc: {result['doc_url']}")
    else:
        print("Failed to generate doc. See logs for details.")
        if 'error' in result:
            logger.error(result.get("error"))

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python main.py /path/to/transcript.json")
        exit(1)
    main(sys.argv[1])