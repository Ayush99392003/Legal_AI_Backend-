# Final Submission: Hybrid Legal RAG & Research Pipeline

This folder contains the complete, validated codebase and research paper for the Hybrid Legal Case Retrieval system.

## Folder Structure

- **`/code`**: Core Python modules for the Level 1-4 retrieval and generation stack.
  - `rag_pipeline.py`: Main entry point for multi-case RAG summaries.
  - `get_case_brief.py`: Utility for single-case deep dives (Facts/Reasoning/Held).
  - `llm_client.py`: Refactored to support **Google Gemini 1.5 Flash**.

## Setup

1.  **API Key**: Copy `.env.example` to `.env` and add your [Google Gemini API Key](https://aistudio.google.com/app/apikey).
2.  **Dependencies**:
    ```bash
    pip install google-generativeai sentence-transformers faiss-cpu rich
    ```
- **`/research_paper`**: 10 Markdown modules ready for academic submission.
  - Includes updated results for N=5,255 and the SC-bias methodological audit.
- **`/benchmarks`**: Raw CSV results and the comprehensive DOCX report.
- **`/docs`**: Final project walkthrough and methodological audit details.

## Quick Start (Demo)

### 1. General RAG Summary
To generate a summarized answer across multiple cases:
```bash
python code/rag_pipeline.py "What are the guidelines for custodial torture compensation?"
```

### 2. Single Case Briefing
To get a detailed IRAC (Facts, Issue, Reasoning) brief for a specific case:
```bash
python code/get_case_brief.py "D.K. Basu v. State of West Bengal"
```

---

## Technical Highlights
- **Hybrid Retrieval**: Standardized on RRF-based fusion (BM25 + MPNet + PageRank).
- **Audit Compliance**: Verified performance against a 10,000-case noise floor to ensure statistical rigor.
- **2025 SOTA Alignment**: Benchmarked against **NyayGraph** and **COLIEE 2024** standards.
