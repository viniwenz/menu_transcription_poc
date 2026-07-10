import pytest

from src.parser import normalize_price, parse_menu_response


# --- parse_menu_response: markdown table -------------------------------------

class TestParseMarkdownTable:
    def test_tabela_simples(self):
        text = (
            "| Produto | Preço |\n"
            "|---------|-------|\n"
            "| X-Burguer | R$ 25,00 |\n"
            "| Fritas | R$ 12,00 |\n"
        )
        result = parse_menu_response(text)
        assert result == [
            {"produto": "X-Burguer", "preco": "R$ 25,00"},
            {"produto": "Fritas", "preco": "R$ 12,00"},
        ]

    def test_tabela_sem_simbolo_real(self):
        text = (
            "| Produto | Preço |\n"
            "|---------|-------|\n"
            "| X-Bacon | 30,00 |\n"
        )
        result = parse_menu_response(text)
        assert result[0]["preco"] == "R$ 30,00"

    def test_tabela_com_nd(self):
        text = (
            "| Produto | Preço |\n"
            "|---------|-------|\n"
            "| Prato do dia | N/D |\n"
        )
        result = parse_menu_response(text)
        assert result[0]["preco"] == "N/D"

    def test_ignora_linhas_fora_da_tabela(self):
        text = (
            "Aqui está o cardápio:\n"
            "| Produto | Preço |\n"
            "|---------|-------|\n"
            "| Suco | R$ 8,00 |\n"
            "\nFim do cardápio.\n"
        )
        result = parse_menu_response(text)
        assert len(result) == 1
        assert result[0]["produto"] == "Suco"


# --- parse_menu_response: JSON -----------------------------------------------

class TestParseJson:
    def test_array_json_simples(self):
        text = '[{"produto": "Pizza", "preco": "R$ 45,00"}]'
        result = parse_menu_response(text)
        assert result == [{"produto": "Pizza", "preco": "R$ 45,00"}]

    def test_json_com_chaves_em_ingles(self):
        text = '[{"name": "Burger", "price": "25.00"}]'
        result = parse_menu_response(text)
        assert result[0]["produto"] == "Burger"
        assert result[0]["preco"] == "R$ 25,00"

    def test_json_dentro_de_bloco_codigo(self):
        text = (
            "Resultado:\n"
            "```json\n"
            '[{"produto": "Salada", "preco": "18,00"}]\n'
            "```\n"
        )
        result = parse_menu_response(text)
        assert result[0]["produto"] == "Salada"

    def test_json_multiline(self):
        text = (
            "[\n"
            '  {"produto": "Café", "preco": "5,00"},\n'
            '  {"produto": "Suco", "preco": "8,00"}\n'
            "]"
        )
        result = parse_menu_response(text)
        assert len(result) == 2


# --- parse_menu_response: plain text -----------------------------------------

class TestParsePlainText:
    def test_separador_traco(self):
        text = "X-Burguer - R$ 25,00\nFritas - R$ 12,00"
        result = parse_menu_response(text)
        assert len(result) == 2
        assert result[0]["produto"] == "X-Burguer"

    def test_separador_dois_pontos(self):
        text = "Refrigerante: R$ 8,00"
        result = parse_menu_response(text)
        assert result[0]["preco"] == "R$ 8,00"

    def test_ignora_linhas_sem_separador(self):
        text = "CARDAPIO\nX-Burguer - R$ 25,00\n"
        result = parse_menu_response(text)
        assert len(result) == 1


# --- normalize_price ---------------------------------------------------------

class TestNormalizePrice:
    @pytest.mark.parametrize("entrada,esperado", [
        ("25,00",      "R$ 25,00"),
        ("25.00",      "R$ 25,00"),
        ("R$ 25,00",   "R$ 25,00"),
        ("R$25,00",    "R$ 25,00"),
        ("1.234,56",   "R$ 1.234,56"),
        ("1,234.56",   "R$ 1.234,56"),
        ("25",         "R$ 25,00"),
        ("N/D",        "N/D"),
        ("ND",         "N/D"),
        ("-",          "N/D"),
        ("",           "N/D"),
    ])
    def test_formatos(self, entrada, esperado):
        assert normalize_price(entrada) == esperado
