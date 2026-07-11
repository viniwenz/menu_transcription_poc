# Menu Transcription POC

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A proof of concept that automatically transcribes restaurant menu photos into
structured data (`{Product, Price}`), using a multimodal LLM (Google Gemini)
and a Gradio interface.

Inspired by DoorDash's engineering blog posts on using LLMs to transcribe
restaurant menu photos:
[Post 1](https://doordash.engineering/2022/09/07/using-llm-to-transcribe-restaurant-menu-photos/) ·
[Post 2](https://doordash.engineering/2023/08/15/how-doordash-uses-ai-models-to-understand-restaurant-menus/)

Developed as the final project ("Desafio Final") for the *Projetista em IA
Generativa* (Generative AI Engineer) Bootcamp at XP Educação (2026).

---

## Problem Statement

Restaurants that want to publish their menu online (delivery apps, websites,
internal systems) usually have to transcribe it by hand from a photo or a PDF
scan — slow, repetitive, and error-prone. This project explores how a
multimodal LLM can read a menu photo directly and return structured,
ready-to-use data, removing that manual step.

---

## Solution Overview

- Image pre-processing (format/size validation, resizing)
- A single multimodal prompt to Gemini asking for a `Produto | Preço` table
- A parser that normalizes the LLM's response (markdown table, JSON, or plain
  text) into a consistent `{produto, preco}` structure
- A guardrails layer that validates the extracted items and automatically
  retries with a refined prompt if the response is malformed
- A Gradio web UI for uploading a photo and viewing the resulting table

## Architecture

```
menu photo
      ↓
 pre-processing (validation, resize)      → src/image_utils.py
      ↓
 Gemini API (multimodal prompt)           → src/llm_client.py
      ↓
 parser → {Produto, Preço} structure       → src/parser.py
      ↓
 guardrails (validation, retry)           → src/guardrails.py
      ↓
 Gradio UI (structured table)             → src/app.py
```

## Project Structure

```
menu-transcription-poc/
├── src/                  # Pipeline modules (image, LLM client, parser, guardrails, UI)
├── tests/                # Unit tests (pytest)
├── notebooks/            # desafio_final.ipynb — official academic deliverable
├── samples/              # Sample menu photos used in tests and the notebook
├── main.py               # Entry point that launches the Gradio app
├── requirements.txt
└── .env.example
```

---

## Getting Started

### Requirements

- Python 3.11
- A free [Gemini API key](https://aistudio.google.com/app/apikey)

### Installation

```bash
git clone https://github.com/viniwenz/menu_transcription_poc.git
cd menu_transcription_poc
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set GEMINI_API_KEY
```

### Running the app

```bash
python main.py
```

Open `http://localhost:7860`, upload a menu photo, and click **Transcrever
Cardápio**.

### Notebook deliverable

`notebooks/desafio_final.ipynb` walks through every pipeline stage with
markdown explanations and was executed end-to-end against the real Gemini
API with two different sample menus — its outputs are already saved, so it
can be reviewed without being re-run.

---

## Application Language

This README is written in English for portfolio purposes. The application
itself, however — the Gradio UI labels, the Gemini system prompt, log
messages, and the transcribed output (product names and prices) — is in
**Portuguese (pt-BR)**, including code comments and docstrings throughout
`src/`.

This is an intentional decision, not an inconsistency: the project is the
deliverable for a Brazilian academic bootcamp, evaluated by a
Portuguese-speaking professor, and built to transcribe real Brazilian
restaurant menus written in Portuguese. Translating the application layer
itself would add no value for its actual audience.

---

## Tech Stack

| Component | Technology |
|---|---|
| Multimodal LLM | Google Gemini (`google-generativeai`) |
| Interface | Gradio |
| Images | Pillow |
| Tests | pytest |
| Notebook | Jupyter |

---

## Author

Vinícius Wenz dos Santos
*Projetista em IA Generativa* Bootcamp — XP Educação
[LinkedIn](https://www.linkedin.com/in/vinicius-wenz-dos-santos/) · [GitHub](https://github.com/viniwenz)

## License

[MIT](LICENSE)
