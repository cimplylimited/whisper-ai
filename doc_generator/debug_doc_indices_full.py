import sys
from utils.auth import get_gdoc_service

def dump_doc_structure_with_indices(doc_id, placeholder="{{OUTLINE_TOC}}"):
    svc = get_gdoc_service()
    doc = svc.documents().get(documentId=doc_id).execute()
    body = doc.get("body", {}).get("content", [])
    print("\n--- FULL PARAGRAPH AND ELEMENT BREAKDOWN ---")
    for p_num, el in enumerate(body):
        para = el.get('paragraph', {})
        if not para: continue
        para_text = ''
        all_run_info = []
        for e_num, seg in enumerate(para.get('elements', [])):
            run = seg.get('textRun', {})
            text = run.get('content', '')
            para_text += text
            si = seg.get('startIndex', None)
            ei = seg.get('endIndex', None)
            match = ""
            if placeholder in text:
                match = "<-- MATCHES OUTLINE PLACEHOLDER"
            if "EXEC" in text or "SUMMAR" in text:
                match += " <-- CONTAINS EXECUTIVE/SUMMARY"
            all_run_info.append(f"    [e{e_num}] {si}-{ei}: {repr(text)} {match}".rstrip())
        if para_text.strip():
            print(f"\n[Paragraph {p_num}]")
            print(f"  Text: {repr(para_text.strip())}")
            for info in all_run_info:
                print(info)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_doc_indices_full.py <GOOGLE_DOC_ID>")
        sys.exit(1)
    dump_doc_structure_with_indices(sys.argv[1])