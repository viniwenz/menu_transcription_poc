import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import DeadlineExceeded, PermissionDenied, ResourceExhausted

from src.llm_client import GeminiClient


# --- helpers -----------------------------------------------------------------

def make_client():
    """Cria GeminiClient com genai mockado. Retorna (client, mock_model)."""
    mock_genai = MagicMock()
    with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            client = GeminiClient()
            # client._model já é mock_genai.GenerativeModel.return_value —
            # mesmo objeto, acessível após sair do with
            return client, mock_genai.GenerativeModel.return_value


def make_response(text: str):
    """Cria um mock de resposta válida da API."""
    response = MagicMock()
    response.text = text
    response.candidates = [MagicMock()]
    return response


# --- GeminiClient.__init__ ---------------------------------------------------

class TestGeminiClientInit:
    def test_raises_sem_api_key(self):
        mock_genai = MagicMock()
        with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                    GeminiClient()

    def test_chama_configure_com_api_key(self):
        mock_genai = MagicMock()
        with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "minha-chave"}):
                GeminiClient()
                mock_genai.configure.assert_called_once_with(api_key="minha-chave")

    def test_usa_modelo_do_env(self):
        mock_genai = MagicMock()
        env = {"GEMINI_API_KEY": "key", "GEMINI_MODEL": "gemini-teste"}
        with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
            with patch.dict(os.environ, env):
                GeminiClient()
                kwargs = mock_genai.GenerativeModel.call_args.kwargs
                assert kwargs["model_name"] == "gemini-teste"


# --- GeminiClient.transcribe_menu --------------------------------------------

class TestTranscribeMenu:
    def test_retorna_texto_da_api(self):
        client, mock_model = make_client()
        tabela = "| Produto | Preço |\n|---------|-------|\n| X-Burguer | R$ 25,00 |"
        mock_model.generate_content.return_value = make_response(tabela)

        result = client.transcribe_menu(b"bytes de imagem")

        assert "X-Burguer" in result
        assert "R$ 25,00" in result

    def test_chama_generate_content_uma_vez(self):
        client, mock_model = make_client()
        mock_model.generate_content.return_value = make_response("| A | B |")

        client.transcribe_menu(b"bytes")

        assert mock_model.generate_content.call_count == 1

    def test_erro_rate_limit(self):
        client, mock_model = make_client()
        mock_model.generate_content.side_effect = ResourceExhausted("429")

        with pytest.raises(RuntimeError, match="Rate limit"):
            client.transcribe_menu(b"bytes")

    def test_erro_timeout(self):
        client, mock_model = make_client()
        mock_model.generate_content.side_effect = DeadlineExceeded("timeout")

        with pytest.raises(RuntimeError, match="Timeout"):
            client.transcribe_menu(b"bytes")

    def test_erro_api_generica(self):
        client, mock_model = make_client()
        mock_model.generate_content.side_effect = PermissionDenied("403")

        with pytest.raises(RuntimeError, match="Erro na API"):
            client.transcribe_menu(b"bytes")

    def test_erro_candidates_vazios(self):
        client, mock_model = make_client()
        response = MagicMock()
        response.candidates = []
        mock_model.generate_content.return_value = response

        with pytest.raises(ValueError, match="filtros de segurança"):
            client.transcribe_menu(b"bytes")

    def test_erro_resposta_vazia(self):
        client, mock_model = make_client()
        response = MagicMock()
        response.candidates = [MagicMock()]
        response.text = "   "
        mock_model.generate_content.return_value = response

        with pytest.raises(ValueError, match="resposta vazia"):
            client.transcribe_menu(b"bytes")
