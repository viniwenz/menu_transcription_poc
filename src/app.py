import logging

import gradio as gr
from PIL import Image

from src.guardrails import transcribe_with_retry
from src.image_utils import encode_image_bytes

logger = logging.getLogger(__name__)

TABLE_HEADERS = ["Produto", "Preço"]


def _get_client():
    from src.llm_client import GeminiClient

    return GeminiClient()


def transcribe_menu_image(image: Image.Image, client=None) -> tuple[list[list[str]], str]:
    """Executa o pipeline completo (validação → API → parser → guardrails).

    Retorna (linhas para a tabela, mensagem de status) — formato aceito
    diretamente pelos componentes Dataframe e Markdown do Gradio.
    """
    if image is None:
        return [], "⚠️ Envie uma foto do cardápio antes de transcrever."

    try:
        # o componente Image do Gradio já garante um PIL.Image decodificado;
        # `img.format` não sobrevive ao pipeline de upload, então validamos
        # só as dimensões aqui (validate_image por formato é para load_image).
        w, h = image.size
        if w == 0 or h == 0:
            raise ValueError("Imagem com dimensões inválidas (largura ou altura = 0).")
        image_bytes = encode_image_bytes(image)
        client = client or _get_client()
        items = transcribe_with_retry(image_bytes, client)
    except Exception as e:
        logger.error("Falha na transcrição: %s", e)
        return [], f"❌ Não foi possível transcrever o cardápio: {e}"

    rows = [[item["produto"], item["preco"]] for item in items]
    return rows, f"✅ {len(rows)} item(ns) encontrado(s)."


def build_interface() -> gr.Blocks:
    with gr.Blocks(title="Menu Transcription POC") as demo:
        gr.Markdown("# 🍽️ Menu Transcription POC")
        gr.Markdown(
            "Envie a foto de um cardápio e a IA transcreve os itens e preços automaticamente."
        )

        image_input = gr.Image(type="pil", label="Foto do cardápio")
        transcribe_btn = gr.Button("Transcrever Cardápio", variant="primary")
        status = gr.Markdown()
        output_table = gr.Dataframe(
            headers=TABLE_HEADERS,
            label="Itens do cardápio",
            wrap=True,
        )

        transcribe_btn.click(
            fn=transcribe_menu_image,
            inputs=image_input,
            outputs=[output_table, status],
        )

    return demo
