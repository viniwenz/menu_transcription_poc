from unittest.mock import MagicMock

from PIL import Image

from src.app import transcribe_menu_image


def make_image(fmt="JPEG", size=(100, 100)):
    """Cria uma PIL Image em memória com `format` preenchido, como faz um upload real."""
    img = Image.new("RGB", size, color=(255, 0, 0))
    img.format = fmt
    return img


class TestTranscribeMenuImage:
    def test_sem_imagem(self):
        rows, status = transcribe_menu_image(None)
        assert rows == []
        assert "Envie uma foto" in status

    def test_sucesso(self):
        client = MagicMock()
        client.transcribe_menu.return_value = (
            "| Produto | Preço |\n|---------|-------|\n| X-Burguer | R$ 25,00 |"
        )

        rows, status = transcribe_menu_image(make_image(), client=client)

        assert rows == [["X-Burguer", "R$ 25,00"]]
        assert "1 item" in status
        assert status.startswith("✅")

    def test_multiplos_itens(self):
        client = MagicMock()
        client.transcribe_menu.return_value = (
            "| Produto | Preço |\n|---------|-------|\n"
            "| X-Burguer | R$ 25,00 |\n"
            "| Fritas | R$ 12,00 |"
        )

        rows, status = transcribe_menu_image(make_image(), client=client)

        assert rows == [["X-Burguer", "R$ 25,00"], ["Fritas", "R$ 12,00"]]
        assert "2 item" in status

    def test_imagem_com_dimensoes_invalidas(self):
        img = Image.new("RGB", (0, 0))

        rows, status = transcribe_menu_image(img, client=MagicMock())

        assert rows == []
        assert status.startswith("❌")

    def test_erro_apos_todas_tentativas(self):
        client = MagicMock()
        client.transcribe_menu.side_effect = RuntimeError("API down")

        rows, status = transcribe_menu_image(make_image(), client=client)

        assert rows == []
        assert status.startswith("❌")

    def test_resposta_sem_itens_validos(self):
        client = MagicMock()
        client.transcribe_menu.return_value = "não é um cardápio"

        rows, status = transcribe_menu_image(make_image(), client=client)

        assert rows == []
        assert status.startswith("❌")
