import sys
from utils.auth import get_gdoc_service

def flatten_text_indices(doc_id):
    svc = get_gdoc_service()
    doc = svc.documents().get(documentId=doc_id).execute()
    body = doc.get("body", {}).get("content", [])

    chars_seen = 0
    para_num = 0
    for el in body:
        para = el.get('paragraph', {})
        if not para: continue
        para_text = ""
        seg_starts = []
        for seg in para.get('elements', []):
            run = seg.get('textRun', {})
            text = run.get('content', '')
            if text.strip() != "":
                para_text += text
                seg_starts.append(chars_seen)
            chars_seen += len(text)

        if para_text.strip():
            print(f"Paragraph {para_num}: [{seg_starts[0] if seg_starts else '?'}] {repr(para_text.rstrip())}")
            para_num += 1

def show_around_index(doc_id, idx, span=40):
    svc = get_gdoc_service()
    doc = svc.documents().get(documentId=doc_id).execute()
    body = doc.get("body", {}).get("content", [])
    flat_text = ''
    for el in body:
        para = el.get('paragraph', {})
        if not para: continue
        for seg in para.get('elements', []):
            run = seg.get('textRun', {})
            text = run.get('content', '')
            flat_text += text
    print(f"\n--- Text context around index {idx}:")
    print(repr(flat_text[max(0, idx-span):idx+span]))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_doc_text_indices.py <GOOGLE_DOC_ID>")
        sys.exit(1)
    doc_id = sys.argv[1]
    flatten_text_indices(doc_id)
    # manually: show_around_index(doc_id, 138)