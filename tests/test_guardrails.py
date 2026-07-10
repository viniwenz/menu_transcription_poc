from unittest.mock import MagicMock

import pytest

from src.guardrails import ValidationResult, transcribe_with_retry, validate_menu


# --- validate_menu -----------------------------------------------------------

class TestValidateMenu:
    def test_lista_valida(self):
        items = [
            {"produto": "X-Burguer", "preco": "R$ 25,00"},
            {"produto": "Fritas", "preco": "N/D"},
        ]
        result = validate_menu(items)
        assert result.valid is True
        assert result.errors == []

    def test_lista_vazia(self):
        result = validate_menu([])
        assert result.valid is False
        assert "Nenhum produto" in result.errors[0]

    def test_produto_com_nome_vazio(self):
        items = [{"produto": "", "preco": "R$ 10,00"}]
        result = validate_menu(items)
        assert result.valid is False
        assert any("nome do produto" in e for e in result.errors)

    def test_preco_invalido(self):
        items = [{"produto": "Pizza", "preco": "caro"}]
        result = validate_menu(items)
        assert result.valid is False
        assert any("inválido" in e for e in result.errors)

    def test_multiplos_erros(self):
        items = [
            {"produto": "", "preco": "invalido"},
            {"produto": "Suco", "preco": "R$ 8,00"},
        ]
        result = validate_menu(items)
        assert result.valid is False
        assert len(result.errors) == 2

    def test_preco_nd_e_valido(self):
        items = [{"produto": "Prato do dia", "preco": "N/D"}]
        result = validate_menu(items)
        assert result.valid is True

    def test_preco_com_milhar(self):
        items = [{"produto": "Cesta", "preco": "R$ 1.234,56"}]
        result = validate_menu(items)
        assert result.valid is True


# --- transcribe_with_retry ---------------------------------------------------

class TestTranscribeWithRetry:
    def _make_client(self, responses: list[str]):
        """Mock de cliente que devolve respostas em sequência."""
        client = MagicMock()
        client.transcribe_menu.side_effect = responses
        return client

    def test_sucesso_na_primeira_tentativa(self):
        resposta = "| Produto | Preço |\n|---------|-------|\n| X-Burguer | R$ 25,00 |"
        client = self._make_client([resposta])

        result = transcribe_with_retry(b"imagem", client)

        assert result == [{"produto": "X-Burguer", "preco": "R$ 25,00"}]
        assert client.transcribe_menu.call_count == 1

    def test_sucesso_na_segunda_tentativa(self):
        invalida = "não é um cardápio"
        valida = "| Produto | Preço |\n|---------|-------|\n| Pizza | R$ 45,00 |"
        client = self._make_client([invalida, valida])

        result = transcribe_with_retry(b"imagem", client, max_attempts=2)

        assert result[0]["produto"] == "Pizza"
        assert client.transcribe_menu.call_count == 2

    def test_segunda_tentativa_usa_retry_prompt(self):
        invalida = "não é um cardápio"
        valida = "| Produto | Preço |\n|---------|-------|\n| Suco | R$ 8,00 |"
        client = self._make_client([invalida, valida])

        transcribe_with_retry(b"imagem", client, max_attempts=2)

        # primeira chamada: sem prompt_override
        assert client.transcribe_menu.call_args_list[0].kwargs.get("prompt_override") is None
        # segunda chamada: com prompt_override preenchido
        assert client.transcribe_menu.call_args_list[1].kwargs.get("prompt_override") is not None

    def test_levanta_erro_apos_todas_tentativas(self):
        client = self._make_client(["inválido", "também inválido"])

        with pytest.raises(ValueError, match="Falha após"):
            transcribe_with_retry(b"imagem", client, max_attempts=2)

    def test_levanta_erro_se_cliente_falhar(self):
        client = MagicMock()
        client.transcribe_menu.side_effect = RuntimeError("API down")

        with pytest.raises(ValueError, match="Falha após"):
            transcribe_with_retry(b"imagem", client, max_attempts=2)
