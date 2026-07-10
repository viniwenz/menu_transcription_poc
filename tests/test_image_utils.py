import base64

import pytest
from PIL import Image

from src.image_utils import encode_image_base64, encode_image_bytes, load_image, validate_image


# --- helpers -----------------------------------------------------------------

def make_image_file(tmp_path, fmt="JPEG", size=(100, 100)):
    """Salva uma imagem real no disco e retorna o path como string."""
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    path = tmp_path / f"test.{ext}"
    Image.new("RGB", size, color=(255, 0, 0)).save(path, format=fmt)
    return str(path)


def open_with_format(tmp_path, fmt):
    """Abre uma imagem do disco para que img.format seja preenchido pelo PIL."""
    return Image.open(make_image_file(tmp_path, fmt))


# --- load_image --------------------------------------------------------------

class TestLoadImage:
    def test_carrega_jpeg(self, tmp_path):
        img = load_image(make_image_file(tmp_path, "JPEG"))
        assert isinstance(img, Image.Image)

    def test_carrega_png(self, tmp_path):
        img = load_image(make_image_file(tmp_path, "PNG"))
        assert isinstance(img, Image.Image)

    def test_carrega_webp(self, tmp_path):
        img = load_image(make_image_file(tmp_path, "WEBP"))
        assert isinstance(img, Image.Image)

    def test_erro_arquivo_nao_encontrado(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_image(str(tmp_path / "nao_existe.jpg"))

    def test_erro_formato_invalido(self, tmp_path):
        path = tmp_path / "fake.jpg"
        path.write_text("isso nao e uma imagem")
        with pytest.raises(ValueError):
            load_image(str(path))

    def test_erro_imagem_corrompida(self, tmp_path):
        # começa com magic bytes de JPEG mas dados truncados
        path = tmp_path / "corrompida.jpg"
        path.write_bytes(b"\xff\xd8\xff" + b"\x00" * 10)
        with pytest.raises(ValueError):
            load_image(str(path))


# --- validate_image ----------------------------------------------------------

class TestValidateImage:
    def test_aceita_jpeg(self, tmp_path):
        validate_image(open_with_format(tmp_path, "JPEG"))  # não deve lançar

    def test_aceita_png(self, tmp_path):
        validate_image(open_with_format(tmp_path, "PNG"))

    def test_aceita_webp(self, tmp_path):
        validate_image(open_with_format(tmp_path, "WEBP"))

    def test_rejeita_formato_nao_suportado(self, tmp_path):
        path = tmp_path / "test.gif"
        Image.new("RGB", (10, 10)).save(path, format="GIF")
        img = Image.open(path)
        with pytest.raises(ValueError, match="não suportado"):
            validate_image(img)

    def test_rejeita_imagem_sem_formato(self):
        # Image.new() em memória não tem format definido (None)
        img = Image.new("RGB", (100, 100))
        with pytest.raises(ValueError):
            validate_image(img)


# --- encode_image_base64 -----------------------------------------------------

class TestEncodeImageBase64:
    def test_retorna_base64_valido(self):
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        result = encode_image_base64(img)
        decoded = base64.b64decode(result)
        assert decoded[:2] == b"\xff\xd8"  # magic bytes de JPEG

    def test_imagem_grande_e_redimensionada(self):
        img = Image.new("RGB", (4000, 3000))
        encode_image_base64(img)
        assert max(img.size) <= 2048

    def test_aceita_imagem_com_transparencia(self):
        img = Image.new("RGBA", (100, 100), color=(0, 0, 255, 128))
        result = encode_image_base64(img)
        assert isinstance(result, str)


# --- encode_image_bytes -------------------------------------------------------

class TestEncodeImageBytes:
    def test_retorna_bytes_jpeg(self):
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        result = encode_image_bytes(img)
        assert isinstance(result, bytes)
        assert result[:2] == b"\xff\xd8"  # magic bytes de JPEG

    def test_imagem_grande_e_redimensionada(self):
        img = Image.new("RGB", (4000, 3000))
        encode_image_bytes(img)
        assert max(img.size) <= 2048
