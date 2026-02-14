#!/usr/bin/env python3
"""
Build FAISS index for IELTS vocabulary words using AWS Bedrock Titan Embeddings.

Usage:
    cd backend && uv run python scripts/build_ielts_index.py
"""

import json
import time
from pathlib import Path

from langchain_community.vectorstores import FAISS

from dotenv import load_dotenv
from langchain_aws import BedrockEmbeddings

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
IELTS_JSON_PATH = PROJECT_ROOT / "IELTS.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data"
FAISS_INDEX_DIR = OUTPUT_DIR / "ielts_index"
PROGRESS_FILE = OUTPUT_DIR / "build_progress.json"

# Titan embedding model (V2 for better multilingual support)
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Batch processing settings to avoid rate limiting
BATCH_SIZE = 50
DELAY_SECONDS = 1.0


def load_progress() -> int:
    """Load the number of already processed words."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
            return data.get("processed_count", 0)
    return 0


def save_progress(processed_count: int):
    """Save the current progress."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"processed_count": processed_count}, f)


def load_ielts_words() -> list[dict]:
    """Load IELTS word list from JSON file."""
    print(f"Loading IELTS words from {IELTS_JSON_PATH}...")
    with open(IELTS_JSON_PATH, "r", encoding="utf-8") as f:
        words = json.load(f)
    print(f"Loaded {len(words)} words")
    return words


def create_embedding_text(word_entry: dict) -> str:
    """Create text to embed for a word entry."""
    word = word_entry["word"]
    definition = word_entry.get("definition", "")
    sentence = word_entry.get("sentence", "")
    collocations = ", ".join(word_entry.get("collocations", []))

    # Combine all fields for richer semantic embedding
    parts = [f"Word: {word}"]
    if definition:
        parts.append(f"Definition: {definition}")
    if sentence:
        parts.append(f"Example: {sentence}")
    if collocations:
        parts.append(f"Collocations: {collocations}")

    return " | ".join(parts)


def create_metadata(word_entry: dict) -> dict:
    """Create metadata dict for a word entry."""
    return {
        "word": word_entry["word"],
        "definition": word_entry.get("definition", ""),
        "sentence": word_entry.get("sentence", ""),
        "collocations": word_entry.get("collocations", []),
    }


def main():
    start_time = time.time()

    # Load words
    words = load_ielts_words()

    # Create texts and metadata for embedding
    print("Creating embedding texts...")
    texts = [create_embedding_text(w) for w in words]
    metadatas = [create_metadata(w) for w in words]

    # Initialize Bedrock embeddings
    print(f"Initializing Bedrock embeddings ({EMBEDDING_MODEL_ID})...")
    embeddings = BedrockEmbeddings(
        model_id=EMBEDDING_MODEL_ID,
    )

    # Check for existing progress
    start_index = load_progress()
    vectorstore = None

    if start_index > 0 and FAISS_INDEX_DIR.exists():
        print(f"Resuming from word {start_index}/{len(texts)}...")
        vectorstore = FAISS.load_local(
            str(FAISS_INDEX_DIR),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    else:
        start_index = 0
        print("Starting fresh...")

    # Skip if already completed
    if start_index >= len(texts):
        print("All words already processed!")
        return

    # Calculate remaining batches
    remaining_texts = texts[start_index:]
    remaining_metadatas = metadatas[start_index:]
    total_batches = (len(remaining_texts) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Processing {len(remaining_texts)} remaining words in {total_batches} batches...")

    # Build FAISS index in batches to avoid rate limiting
    for i in range(0, len(remaining_texts), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch_texts = remaining_texts[i: i + BATCH_SIZE]
        batch_metadatas = remaining_metadatas[i: i + BATCH_SIZE]

        print(f"  Processing batch {batch_num}/{total_batches}...", end=" ", flush=True)

        if vectorstore is None:
            vectorstore = FAISS.from_texts(
                texts=batch_texts,
                embedding=embeddings,
                metadatas=batch_metadatas,
            )
        else:
            vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)

        # Save progress after each batch
        processed_count = start_index + i + len(batch_texts)
        save_progress(processed_count)
        vectorstore.save_local(str(FAISS_INDEX_DIR))

        print(f"done (saved: {processed_count}/{len(texts)})")

        # Delay between batches to avoid rate limiting (skip after last batch)
        if i + BATCH_SIZE < len(remaining_texts):
            time.sleep(DELAY_SECONDS)

    # Clean up progress file when complete
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
        print("Progress file cleaned up.")

    elapsed_time = time.time() - start_time
    print(f"\nDone! Total time: {elapsed_time:.2f} seconds")
    print(f"Index saved to: {FAISS_INDEX_DIR}")


if __name__ == "__main__":
    main()
