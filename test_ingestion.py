#!/usr/bin/env python3
"""
Test script to verify ingestion is working properly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ingestion.ingest_expert import ingest_expert_knowledge

# Test with a small, well-known repository
print("Testing ingestion with a small repository...\n")

result = ingest_expert_knowledge(
    expert_type="frontend",
    repo_url="https://github.com/shadcn-ui/ui",
    verbose=True
)

print("\n" + "="*70)
print("RESULT:")
print("="*70)
print(f"Success: {result.get('success')}")
print(f"Files processed: {result.get('files_processed', 0)}")
print(f"Chunks created: {result.get('chunks_created', 0)}")
print(f"Vectors stored: {result.get('vectors_stored', 0)}")
if result.get('error'):
    print(f"Error: {result.get('error')}")
print("="*70)

if result.get('success'):
    print("\n✅ Ingestion is working! You can now run ingest_all_brains.py")
else:
    print("\n❌ Ingestion failed. Check the error above.")
    print("\nCommon issues:")
    print("  1. Git not installed or not in PATH")
    print("  2. Network connection issues")
    print("  3. ChromaDB not initialized")
    print("  4. Missing dependencies")

