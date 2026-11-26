"""
Krishi Sakhi Knowledge Base Ingestion Script
Scans data/knowledge_base/ for PDFs, extracts text, chunks semantically,
and produces processed_chunks.json and knowledge_manifest.json for Step 5 (RAG + FAISS).
"""

import os
import sys
import json
from datetime import datetime

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from utils.pdf_processor import process_pdf

KB_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")
OUTPUT_CHUNKS_FILE = os.path.join(KB_DIR, "processed_chunks.json")
OUTPUT_MANIFEST_FILE = os.path.join(KB_DIR, "knowledge_manifest.json")


def scan_and_ingest():
    print("=" * 60)
    print("[KRISHI SAKHI] - AGRICULTURE KNOWLEDGE BASE INGESTION")
    print("=" * 60)
    print(f"Scanning directory: {KB_DIR}")

    if not os.path.exists(KB_DIR):
        print(f"Error: Knowledge base directory does not exist: {KB_DIR}")
        return

    all_chunks = []
    doc_stats = []
    categories_found = set()

    for root, dirs, files in os.walk(KB_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                full_path = os.path.join(root, file)
                # Category is the immediate parent subfolder name
                rel_dir = os.path.relpath(root, KB_DIR)
                category = rel_dir if rel_dir != "." else "general"
                categories_found.add(category)

                print(f"\nProcessing [{category}]: {file}...")
                try:
                    chunks = process_pdf(full_path, category=category)
                    pages_seen = len(set(c["page"] for c in chunks))
                    all_chunks.extend(chunks)

                    doc_stats.append({
                        "file_name": file,
                        "relative_path": os.path.relpath(full_path, BASE_DIR),
                        "category": category,
                        "pages": pages_seen,
                        "chunks_count": len(chunks),
                        "total_characters": sum(c["char_count"] for c in chunks)
                    })
                    print(f"  -> Extracted {pages_seen} page(s), created {len(chunks)} semantic chunks.")
                except Exception as e:
                    print(f"  -> ERROR processing {file}: {e}")

    # Build manifest
    manifest = {
        "status": "ready_for_rag",
        "last_ingested_at": datetime.now().isoformat(),
        "total_documents": len(doc_stats),
        "total_chunks": len(all_chunks),
        "categories": sorted(list(categories_found)),
        "documents": doc_stats
    }

    # Save processed_chunks.json
    with open(OUTPUT_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Saved {len(all_chunks)} chunks to: {OUTPUT_CHUNKS_FILE}")

    # Save knowledge_manifest.json
    with open(OUTPUT_MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved knowledge manifest to: {OUTPUT_MANIFEST_FILE}")

    print("\n" + "=" * 60)
    print("INGESTION SUMMARY:")
    print(f"• Total Agricultural Documents : {manifest['total_documents']}")
    print(f"• Categories Covered          : {', '.join(manifest['categories'])}")
    print(f"• Total Chunks Generated      : {manifest['total_chunks']}")
    print("=" * 60)
    print("Step 4 complete! Knowledge base is fully prepared for Step 5 (FAISS Embeddings).\n")


if __name__ == "__main__":
    scan_and_ingest()
