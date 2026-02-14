# IELTS RAG Feature Summary

> 此文件記錄 IELTS 單字建議功能的設計討論與決策，供未來實作參考。

## Feature Overview

在 `/summary` endpoint 新增一個「如果你正在準備雅思...」section，透過 RAG 流程針對對話中的 corrections 給出 IELTS 官方單字的替換建議。

### 目標

- 確保建議的單字都來自**官方 IELTS 單字表**（約 5000 字）
- 提供準確的定義和例句
- 幫助使用者學習更高級的詞彙表達

---

## Architecture

```
                         POST /summary
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│   corrections = [                                                               │
│     {original: "I go store", corrected: "I went to the store", ...},           │
│     {original: "She have cat", corrected: "She has a cat", ...}                │
│   ]                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────────────────────────┐
│  現有 tips 生成       │              │          IELTS RAG Pipeline              │
│  (Sonnet)            │              │                                          │
└──────────┬───────────┘              │  ┌────────────────────────────────────┐  │
           │                          │  │ Step 1: Keyword Extraction (Haiku) │  │
           │                          │  │                                    │  │
           │                          │  │ Input: corrected sentences         │  │
           │                          │  │ Output: replaceable_words +        │  │
           │                          │  │         topic_keywords             │  │
           │                          │  └─────────────────┬──────────────────┘  │
           │                          │                    │                     │
           │                          │                    ▼                     │
           │                          │  ┌────────────────────────────────────┐  │
           │                          │  │ Step 2: Vector Search (FAISS)      │  │
           │                          │  │                                    │  │
           │                          │  │ 5000 IELTS words (Titan Embedding) │  │
           │                          │  │ Query: keywords → Top-K results    │  │
           │                          │  └─────────────────┬──────────────────┘  │
           │                          │                    │                     │
           │                          │                    ▼                     │
           │                          │  ┌────────────────────────────────────┐  │
           │                          │  │ Step 3: Generate Suggestions       │  │
           │                          │  │ (Sonnet)                           │  │
           │                          │  │                                    │  │
           │                          │  │ Input: sentences + retrieved words │  │
           │                          │  │ Output: replacement suggestions    │  │
           │                          │  └─────────────────┬──────────────────┘  │
           │                          │                    │                     │
           │                          └────────────────────┼─────────────────────┘
           │                                               │
           └───────────────────┬───────────────────────────┘
                               │
                               ▼
                    SummaryResponse {
                      corrections,
                      tips,
                      common_patterns,
                      ielts_suggestions    ◄── NEW
                    }
```

---

## Technical Decisions

### 1. Input Source

| Decision | Use `corrected` sentences                                           |
| -------- | ------------------------------------------------------------------- |
| Reason   | 原始句子可能有文法錯誤，corrected 版本更適合做 embedding 和語意分析 |

### 2. Trigger Timing

| Decision | Real-time on each `/summary` call |
| -------- | --------------------------------- |
| Reason   | 簡單直接，不需要額外的 state 管理 |

### 3. Vector Store

| Decision | FAISS (in-memory)                        |
| -------- | ---------------------------------------- |
| Reason   | 5000 單字規模小，FAISS 足夠且 latency 低 |

### 4. Embedding Model

| Decision | AWS Bedrock Titan Embedding |
| -------- | --------------------------- |
| Reason   | 與 AWS 架構整合             |

### 5. LLM Strategy

| Step                  | Model         | Reason                       |
| --------------------- | ------------- | ---------------------------- |
| Keyword Extraction    | Claude Haiku  | 便宜、快速，任務簡單         |
| Suggestion Generation | Claude Sonnet | 需要較強的語言理解和生成能力 |

### 6. Edge Case: Empty Corrections

| Decision | Skip IELTS section entirely                                  |
| -------- | ------------------------------------------------------------ |
| Reason   | 沒有 corrections 代表沒有需要改進的句子，不需要進行 RAG 流程 |

---

## FAISS Index Lifecycle

採用**預先建立 index** 的方式：

```
[一次性腳本 - build_ielts_index.py]
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ IELTS.json  │ ──► │ Titan Embed  │ ──► │ Save to     │
│ (5000 words)│     │ (batch)      │     │ ielts.faiss │
└─────────────┘     └──────────────┘     └─────────────┘

[Server 啟動]
┌─────────────┐     ┌──────────────┐
│ Server      │ ──► │ Load         │ ──► FAISS Index ready (~100ms)
│ Start       │     │ ielts.faiss  │
└─────────────┘     └──────────────┘
```

### IELTS 單字 Chunk Format

```
Word: [{word}]. Definition: {definition}. Example: {sentence}
```

Example:

```
Word: [abandon]. Definition: To leave a place, thing, or person, usually for ever. Example: How could she abandon her own child?
```

---

## Keyword Extraction Output Format

Haiku 需要同時擷取兩種關鍵字：

```json
{
  "replaceable_words": ["store", "cat", "went"],
  "topic_keywords": ["shopping", "pets", "daily activities"]
}
```

| Type                | Purpose                                     |
| ------------------- | ------------------------------------------- |
| `replaceable_words` | 句子中可以被替換成更高級詞彙的一般詞        |
| `topic_keywords`    | 句子的主題，用於找相關 IELTS 詞彙來豐富表達 |

---

## Vector Search Strategy

使用 **關鍵字直接搜尋**：

```
query = "store"
results = [
  "Word: [shop]. Definition: ...",
  "Word: [purchase]. Definition: ...",
  "Word: [retail]. Definition: ..."
]
```

---

## Output Format

### New Field in SummaryResponse

```python
class IELTSSuggestion(BaseModel):
    original_sentence: str
    target_word: str
    suggestions: list[WordSuggestion]

class WordSuggestion(BaseModel):
    word: str
    definition: str
    example: str
    improved_sentence: str
```

### Example Response

```json
{
  "corrections": [...],
  "tips": "...",
  "common_patterns": [...],
  "ielts_suggestions": [
    {
      "original_sentence": "I went to the store yesterday",
      "target_word": "store",
      "suggestions": [
        {
          "word": "outlet",
          "definition": "A shop that sells goods...",
          "example": "Factory outlets offer discounted prices.",
          "improved_sentence": "I went to the outlet yesterday"
        }
      ]
    }
  ]
}
```

---

## Files to Create/Modify

### New Files

| File                                   | Purpose                                   |
| -------------------------------------- | ----------------------------------------- |
| `backend/scripts/build_ielts_index.py` | 一次性腳本，建立 FAISS index              |
| `backend/ielts_rag.py`                 | IELTS RAG pipeline 邏輯                   |
| `backend/data/ielts.faiss`             | 預建立的 FAISS index                      |
| `backend/data/ielts_metadata.json`     | 單字 metadata (word, definition, example) |
| `IELTS.json`                           | IELTS 單字表原始資料 (5000 words)         |

### Modified Files

| File                        | Changes                                         |
| --------------------------- | ----------------------------------------------- |
| `backend/schemas/chat.py`   | 新增 `IELTSSuggestion`, `WordSuggestion` schema |
| `backend/endpoints/chat.py` | `/summary` endpoint 整合 IELTS RAG pipeline     |
| `backend/dependencies.py`   | 新增 FAISS index 的 dependency injection        |

---

## Environment Variables

```bash
# .env
AWS_REGION=us-east-1  # or your Bedrock region
# Bedrock credentials (via AWS profile or IAM role)
```

---

## Open Questions for Implementation

1. **Top-K value**: Vector search 每個 keyword 要取幾個結果？(建議: 3-5)
2. **Similarity threshold**: 是否需要設定最低相似度門檻？
3. **Rate limiting**: Bedrock Titan Embedding 的 rate limit 考量
4. **Caching**: 是否需要 cache 常見 keyword 的搜尋結果？

---

## References

- [FAISS Documentation](https://faiss.ai/)
- [AWS Bedrock Titan Embedding](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
- [LangChain FAISS Integration](https://python.langchain.com/docs/integrations/vectorstores/faiss)
