import base64
import os

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """Você é um assistente especializado em transcrição de cardápios de restaurantes.
Analise a imagem do cardápio e extraia todos os itens com seus respectivos preços.

Retorne os dados em formato de tabela markdown com exatamente duas colunas:

| Produto | Preço |
|---------|-------|
| Nome do item | R$ XX,XX |

Regras:
- Inclua todos os itens visíveis no cardápio
- Mantenha os nomes dos produtos exatamente como aparecem
- Normalize os preços no formato R$ XX,XX
- Se um preço não estiver visível, use "N/D"
- Não adicione texto antes ou depois da tabela
"""


class GeminiClient:
    def __init__(self):
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente.")

        genai.configure(api_key=api_key)

        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
        max_tokens = int(os.getenv("GEMINI_MAX_TOKENS", "1024"))

        self._model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

    def transcribe_menu(self, image_bytes: bytes) -> str:
        """Envia imagem para o Gemini e retorna texto com tabela Produto | Preço."""
        from google.api_core import exceptions as google_exceptions

        image_part = {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_bytes).decode("utf-8"),
            }
        }

        try:
            response = self._model.generate_content([SYSTEM_PROMPT, image_part])
        except google_exceptions.ResourceExhausted:
            raise RuntimeError("Rate limit atingido. Aguarde alguns segundos e tente novamente.")
        except google_exceptions.DeadlineExceeded:
            raise RuntimeError("Timeout na chamada à API Gemini.")
        except google_exceptions.GoogleAPICallError as e:
            raise RuntimeError(f"Erro na API Gemini: {e}")

        if not response.candidates:
            raise ValueError("Resposta bloqueada pelos filtros de segurança da API.")

        text = response.text.strip()
        if not text:
            raise ValueError("A API retornou uma resposta vazia.")

        return text
