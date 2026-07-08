# Menu Transcription POC

Prova de conceito de transcrição automática de cardápios de restaurante a partir de fotos, usando LLM multimodal (Google Gemini) + interface Gradio.

Inspirado no pipeline da [DoorDash](https://doordash.engineering/2022/09/07/using-llm-to-transcribe-restaurant-menu-photos/).

## Arquitetura

```
foto do cardápio
      ↓
 pré-processamento (validação, resize)
      ↓
 Gemini API (multimodal prompt)
      ↓
 parser → estrutura {Produto, Preço}
      ↓
 guardrails (validação, retry)
      ↓
 Gradio UI (tabela estruturada)
```

## Instalação

```bash
git clone <repo-url>
cd menu-transcription-poc
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edite .env com sua GEMINI_API_KEY
```

## Como usar

```bash
python main.py
```

Acesse `http://localhost:7860`, faça upload de uma foto de cardápio e clique em **Transcrever Cardápio**.

## Stack

| Componente | Tecnologia |
|---|---|
| LLM multimodal | Google Gemini (`google-generativeai`) |
| Interface | Gradio |
| Imagens | Pillow |
| Testes | pytest |
| Notebook | Jupyter |

## Desafio Final

Este projeto é a entrega do Desafio Final do Bootcamp **Projetista em IA Generativa** da XP Educação.

O notebook de entrega está em `notebooks/desafio_final.ipynb`.
