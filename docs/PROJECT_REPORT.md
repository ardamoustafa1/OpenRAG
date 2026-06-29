# Project Report

## Purpose

This project implements the PDF assignment: a local Q&A knowledge assistant using the RAG pattern, SQLite for local document and vector storage, and a Microsoft Foundry Local compatible model layer.

## How It Works

1. Documents in `knowledge_base/` are split into passage-level chunks.
2. Each chunk is embedded and stored in `data/rag.sqlite3`.
3. A user asks a question through the CLI or localhost web UI.
4. The question is embedded and compared with stored vectors using cosine similarity.
5. The top chunks are inserted into a grounded prompt.
6. The assistant answers using Foundry Local when available, or a fully local deterministic fallback for tests.

## Design Decisions

- SQLite was selected because the project is local, beginner-friendly, and small enough for Python-based vector scoring.
- The web UI binds only to `127.0.0.1` so the application remains a local demo.
- The model adapter is isolated in `foundry.py`, making the rest of the RAG pipeline testable without external APIs.
- The fallback backend exists only to keep the app runnable and testable on a machine where Foundry Local has not been installed yet. It does not use cloud services.

## Limitations

- The JSON vector storage approach is simple and correct for a small knowledge base, but not optimized for thousands of documents.
- Foundry Local model aliases can vary by SDK/catalog version, so model aliases are centralized in `config.py`.
- The local fallback is extractive and not a replacement for the final Foundry Local model demo.

## Demo Script

1. Index the local documents.
2. Ask an answerable question from the student's own document set.
3. Show the retrieved source metadata.
4. Ask a question that is intentionally absent from the document set.
5. Confirm the assistant declines to guess when the answer is missing.
