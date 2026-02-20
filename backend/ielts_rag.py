"""
IELTS RAG Pipeline for vocabulary suggestions.

This module provides the core RAG pipeline that:
1. Extracts keywords from corrected sentences using Claude Haiku
2. Searches FAISS index for relevant IELTS vocabulary
3. Generates vocabulary suggestions using Claude Sonnet
"""

import json
import logging
from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage

from utils import strip_markdown_code_blocks

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Embedding model - must match the one used to build the index
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Number of similar words to retrieve per keyword
TOP_K_RESULTS = 1


class ExtractedKeywords(TypedDict):
    """Keywords extracted from corrected sentences."""
    replaceable_words: list[str]  # Words that could be replaced with IELTS vocabulary
    topic_keywords: list[str]  # Topic-related keywords for context


class WordSuggestion(TypedDict):
    """A single IELTS vocabulary suggestion."""
    target_word: str  # The word being replaced
    ielts_word: str  # The suggested IELTS word
    definition: str  # Definition of the IELTS word
    example: str  # Example sentence from IELTS word list
    improved_sentence: str  # The corrected sentence with IELTS word substituted


class IELTSSuggestions(TypedDict):
    """Result of the IELTS RAG pipeline."""
    suggestions: list[WordSuggestion]


async def extract_keywords(corrected_sentences: list[str]) -> ExtractedKeywords:
    """
    Extract replaceable words and topic keywords from corrected sentences.

    Uses Claude Haiku for fast, cost-effective extraction.

    Args:
        corrected_sentences: List of grammar-corrected sentences from user

    Returns:
        ExtractedKeywords with replaceable_words and topic_keywords
    """
    if not corrected_sentences:
        return {"replaceable_words": [], "topic_keywords": []}

    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0.0,  # Deterministic for consistent extraction
    )

    system_prompt = """Extract vocabulary from the given sentences for IELTS vocabulary enhancement.

Output JSON with two arrays:
1. "replaceable_words": Common words that could be replaced with more advanced IELTS vocabulary (nouns, verbs, adjectives, adverbs). Focus on simple/basic words like "store", "big", "good", "go", "make", etc.
2. "topic_keywords": Abstract topic/theme keywords to find related vocabulary (e.g., "shopping", "education", "technology")

Rules:
- Only include words actually present in the sentences for replaceable_words
- Extract 3-5 replaceable words maximum
- Extract 1-3 topic keywords
- Ignore function words (the, a, is, etc.)

Example input: "I went to the store yesterday and bought many things."
Example output:
{
  "replaceable_words": ["store", "bought", "things"],
  "topic_keywords": ["shopping", "daily activities"]
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
            "topic_keywords": result.get("topic_keywords", [])
        }
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Keyword extraction failed: {e}")
        return {"replaceable_words": [], "topic_keywords": []}


async def search_ielts_vocabulary(
    keywords: ExtractedKeywords,
    faiss_index: FAISS,
) -> list[dict]:
    """
    Search FAISS index for relevant IELTS vocabulary alternatives.

    Args:
        keywords: Extracted keywords from corrected sentences
        faiss_index: Pre-loaded FAISS index with IELTS vocabulary

    Returns:
        List of relevant IELTS word entries with metadata
    """
    if not keywords["replaceable_words"] and not keywords["topic_keywords"]:
        return []

    # Combine all keywords for semantic search
    all_keywords = keywords["replaceable_words"] + keywords["topic_keywords"]

    results = []
    seen_words = set()

    for keyword in all_keywords[:3]:  # Limit to first 3 keywords
        try:
            # Perform similarity search
            docs = await faiss_index.asimilarity_search(keyword, k=TOP_K_RESULTS)

            for doc in docs:
                print('search output doc', doc)
                word = doc.metadata.get("word", "")
                # Skip duplicates and the keyword itself
                if word.lower() in seen_words or word.lower() == keyword.lower():
                    continue

                seen_words.add(word.lower())
                results.append({
                    "word": word,
                    "definition": doc.metadata.get("definition", ""),
                    "sentence": doc.metadata.get("sentence", ""),
                    "collocations": doc.metadata.get("collocations", []),
                    "source_keyword": keyword,
                })
        except Exception as e:
            logger.warning(f"FAISS search failed for keyword '{keyword}': {e}")
            continue

    return results


async def generate_suggestions(
    corrected_sentences: list[str],
    keywords: ExtractedKeywords,
    vocabulary_matches: list[dict],
) -> list[WordSuggestion]:
    """
    Generate vocabulary suggestions using Claude Sonnet.

    Creates contextual suggestions that show how to use IELTS vocabulary
    in place of simpler words.

    Args:
        corrected_sentences: Original corrected sentences from user
        keywords: Extracted keywords (with replaceable_words)
        vocabulary_matches: IELTS vocabulary matches from FAISS search

    Returns:
        List of WordSuggestion with target_word, ielts_word, definition, example, improved_sentence
    """
    if not vocabulary_matches or not keywords["replaceable_words"]:
        return []

    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.3,  # Slightly creative for natural suggestions
    )

    system_prompt = """You are an IELTS vocabulary coach. Given a user's sentences and IELTS vocabulary options, create helpful word substitution suggestions.

For each suggestion, provide:
- target_word: The simpler word being replaced (must be from the user's sentences)
- ielts_word: The IELTS vocabulary alternative
- definition: Brief definition of the IELTS word
- example: The example sentence from the IELTS word list
- improved_sentence: Rewrite ONE of the user's sentences using the IELTS word naturally

Rules:
- Only suggest substitutions that make sense in context
- Keep improved sentences natural - don't force awkward word usage
- Provide 2-4 suggestions maximum
- Each target_word must actually appear in the user's sentences

Output valid JSON array of suggestions:
[
  {
    "target_word": "store",
    "ielts_word": "outlet",
    "definition": "A shop or store, especially one selling specific goods",
    "example": "The factory outlet offers discounted prices.",
    "improved_sentence": "I went to the outlet yesterday."
  }
]

Output valid JSON only, no other text."""

    combined_sentences = " ".join(corrected_sentences)

    # Format vocabulary matches for the prompt
    vocab_info = "\n".join([
        f"- {v['word']}: {v['definition']} (Example: {v['sentence']})"
        for v in vocabulary_matches[:3]  # Limit context size
    ])

    user_content = f"""User's sentences: {combined_sentences}

Replaceable words: {', '.join(keywords['replaceable_words'])}

Available IELTS vocabulary:
{vocab_info}

Generate suggestions for substituting simpler words with IELTS vocabulary."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content if isinstance(
            response.content, str) else str(response.content)
        content = strip_markdown_code_blocks(content)

        suggestions = json.loads(content)

        # Validate and convert to WordSuggestion format
        valid_suggestions: list[WordSuggestion] = []
        for s in suggestions:
            if all(k in s for k in ["target_word", "ielts_word", "definition", "example", "improved_sentence"]):
                valid_suggestions.append({
                    "target_word": s["target_word"],
                    "ielts_word": s["ielts_word"],
                    "definition": s["definition"],
                    "example": s["example"],
                    "improved_sentence": s["improved_sentence"],
                })

        return valid_suggestions[:4]  # Maximum 4 suggestions

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Suggestion generation failed: {e}")
        return []


async def run_ielts_rag_pipeline(
    corrected_sentences: list[str],
    faiss_index: FAISS,
) -> IELTSSuggestions:
    """
    Main pipeline function that orchestrates the IELTS RAG workflow.

    Pipeline steps:
    1. Extract keywords from corrected sentences (Haiku)
    2. Search FAISS index for relevant IELTS vocabulary
    3. Generate vocabulary suggestions (Sonnet)

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

        if not keywords["replaceable_words"] and not keywords["topic_keywords"]:
            return {"suggestions": []}

        # Step 2: Search FAISS index for vocabulary matches
        vocabulary_matches = await search_ielts_vocabulary(keywords, faiss_index)
        logger.debug(f"Found {len(vocabulary_matches)} vocabulary matches")

        if not vocabulary_matches:
            return {"suggestions": []}

        # Step 3: Generate suggestions using Claude Sonnet
        suggestions = await generate_suggestions(
            corrected_sentences,
            keywords,
            vocabulary_matches,
        )
        logger.debug(f"Generated {len(suggestions)} suggestions")

        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"IELTS RAG pipeline failed: {e}", exc_info=True)
        return {"suggestions": []}
