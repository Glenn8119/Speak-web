"""
IELTS RAG Pipeline for vocabulary suggestions.

This module provides the core RAG pipeline that:
1. Extracts keywords from corrected sentences using Claude Haiku
2. Searches FAISS index for relevant IELTS vocabulary
3. Generates usage context explanations using Claude Haiku
"""

import json
import logging
from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage

from utils import strip_markdown_code_blocks

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Number of similar words to retrieve per keyword
TOP_K_RESULTS = 1

# Score threshold for filtering low-relevance results
# FAISS L2 distance: lower = more similar. Typical range 0.3-1.5
SCORE_THRESHOLD = 1.3


class ExtractedKeywords(TypedDict):
    """Keywords extracted from corrected sentences."""
    replaceable_words: list[str]  # Words that could be replaced with IELTS vocabulary


class WordSuggestion(TypedDict):
    """A single IELTS vocabulary suggestion."""
    target_word: str  # The word being replaced (from user's sentence)
    ielts_word: str  # The suggested IELTS word
    definition: str  # Definition of the IELTS word
    example: str  # Example sentence from IELTS word list
    usage_context: str  # When/how to use this word vs the simple word


class IELTSSuggestions(TypedDict):
    """Result of the IELTS RAG pipeline."""
    suggestions: list[WordSuggestion]


async def extract_keywords(corrected_sentences: list[str]) -> ExtractedKeywords:
    """
    Extract replaceable words from corrected sentences.

    Uses Claude Haiku for fast, cost-effective extraction.

    Args:
        corrected_sentences: List of grammar-corrected sentences from user

    Returns:
        ExtractedKeywords with replaceable_words
    """
    if not corrected_sentences:
        return {"replaceable_words": []}

    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0.0,  # Deterministic for consistent extraction
    )

    system_prompt = """Extract vocabulary from the given sentences for IELTS vocabulary enhancement.

Output JSON with one array:
- "replaceable_words": Common words that could be replaced with more advanced IELTS vocabulary (nouns, verbs, adjectives, adverbs). Focus on simple/basic words like "store", "big", "good", "go", "make", etc.

Rules:
- Only include words actually present in the sentences
- Extract 3-5 replaceable words maximum
- Ignore function words (the, a, is, etc.)

Example input: "I went to the store yesterday and bought many things."
Example output:
{
  "replaceable_words": ["store", "bought", "things"]
}

Output valid JSON only, no other text."""

    combined_text = " ".join(corrected_sentences)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Sentences: {combined_text}")
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content if isinstance(
            response.content, str) else str(response.content)
        content = strip_markdown_code_blocks(content)

        result = json.loads(content)
        return {
            "replaceable_words": result.get("replaceable_words", []),
        }
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Keyword extraction failed: {e}")
        return {"replaceable_words": []}


async def search_ielts_vocabulary(
    keywords: ExtractedKeywords,
    faiss_index: FAISS,
) -> list[WordSuggestion]:
    """
    Search FAISS index for relevant IELTS vocabulary alternatives.

    Args:
        keywords: Extracted keywords from corrected sentences
        faiss_index: Pre-loaded FAISS index with IELTS vocabulary

    Returns:
        List of WordSuggestion with target_word, ielts_word, definition, example
    """
    if not keywords["replaceable_words"]:
        return []

    results: list[dict] = []
    seen_words = set()

    for keyword in keywords["replaceable_words"][:4]:  # Limit to first 4 keywords
        try:
            # Perform similarity search with scores
            docs_with_scores = await faiss_index.asimilarity_search_with_score(
                keyword, k=TOP_K_RESULTS
            )

            for doc, score in docs_with_scores:
                logger.debug(
                    f"FAISS search result for '{keyword}': {doc.metadata.get('word')} "
                    f"(score: {score:.3f})"
                )

                # Filter out low-relevance results (higher score = less similar)
                if score > SCORE_THRESHOLD:
                    logger.debug(
                        f"Skipping '{doc.metadata.get('word')}' - "
                        f"score {score:.3f} exceeds threshold {SCORE_THRESHOLD}"
                    )
                    continue

                word = doc.metadata.get("word", "")
                # Skip duplicates and the keyword itself
                if word.lower() in seen_words or word.lower() == keyword.lower():
                    continue

                seen_words.add(word.lower())
                results.append({
                    "target_word": keyword,
                    "ielts_word": word,
                    "definition": doc.metadata.get("definition", ""),
                    "example": doc.metadata.get("sentence", ""),
                })
        except Exception as e:
            logger.warning(f"FAISS search failed for keyword '{keyword}': {e}")
            continue

    return results


async def generate_usage_explanations(
    vocabulary_matches: list[dict],
) -> list[WordSuggestion]:
    """
    Generate usage context explanations for vocabulary suggestions.

    Uses Claude Haiku to explain when/how to use each IELTS word
    compared to the simpler alternative.

    Args:
        vocabulary_matches: List of vocabulary matches from FAISS search

    Returns:
        List of WordSuggestion with usage_context filled in
    """
    if not vocabulary_matches:
        return []

    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0.3,
    )

    system_prompt = """You are an English vocabulary coach helping learners expand their vocabulary.

For each word pair, explain WHEN and WHERE to use the advanced word vs the simple word.
Focus on practical usage scenarios (casual speech vs formal writing, specific contexts).

Output JSON array with usage_context for each word:
[
  {
    "target_word": "store",
    "ielts_word": "establishment",
    "usage_context": "Use 'store' in casual conversation. 'Establishment' is more formal, suitable for IELTS writing, business reports, or when describing institutions."
  }
]

Rules:
- Keep explanations concise (1-2 sentences in English)
- Be practical - focus on real usage scenarios
- Don't be preachy - just explain the difference

Output valid JSON only."""

    word_pairs = "\n".join([
        f"- {v['target_word']} → {v['ielts_word']} ({v['definition']})"
        for v in vocabulary_matches
    ])

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"Generate usage context for these word pairs:\n{word_pairs}")
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content if isinstance(
            response.content, str) else str(response.content)
        content = strip_markdown_code_blocks(content)

        explanations = json.loads(content)

        # Build a map of usage contexts
        context_map = {
            e["target_word"]: e.get("usage_context", "")
            for e in explanations
            if "target_word" in e
        }

        # Merge usage_context into vocabulary matches
        result: list[WordSuggestion] = []
        for v in vocabulary_matches:
            result.append({
                "target_word": v["target_word"],
                "ielts_word": v["ielts_word"],
                "definition": v["definition"],
                "example": v["example"],
                "usage_context": context_map.get(v["target_word"], ""),
            })

        return result

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Usage explanation generation failed: {e}")
        # Return without usage_context on failure
        return [
            {
                "target_word": v["target_word"],
                "ielts_word": v["ielts_word"],
                "definition": v["definition"],
                "example": v["example"],
                "usage_context": "",
            }
            for v in vocabulary_matches
        ]


async def run_ielts_rag_pipeline(
    corrected_sentences: list[str],
    faiss_index: FAISS,
) -> IELTSSuggestions:
    """
    Main pipeline function that orchestrates the IELTS RAG workflow.

    Pipeline steps:
    1. Extract keywords from corrected sentences (Haiku)
    2. Search FAISS index for relevant IELTS vocabulary
    3. Generate usage context explanations (Haiku)

    Args:
        corrected_sentences: List of grammar-corrected sentences from conversation
        faiss_index: Pre-loaded FAISS index with IELTS vocabulary embeddings

    Returns:
        IELTSSuggestions with vocabulary suggestions, or empty suggestions on failure
    """
    if not corrected_sentences:
        return {"suggestions": []}

    try:
        # Step 1: Extract keywords using Claude Haiku
        keywords = await extract_keywords(corrected_sentences)
        logger.debug(f"Extracted keywords: {keywords}")

        if not keywords["replaceable_words"]:
            return {"suggestions": []}

        # Step 2: Search FAISS index for vocabulary matches
        vocabulary_matches = await search_ielts_vocabulary(keywords, faiss_index)
        logger.debug(f"Found {len(vocabulary_matches)} vocabulary matches")

        if not vocabulary_matches:
            return {"suggestions": []}

        # Step 3: Generate usage context explanations
        suggestions = await generate_usage_explanations(vocabulary_matches)
        logger.debug(
            f"Generated {len(suggestions)} suggestions with usage context")

        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"IELTS RAG pipeline failed: {e}", exc_info=True)
        return {"suggestions": []}
