import base64
import io
from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_SIZE_PX = 2048


def load_image(path: str) -> Image.Image:
    """Carrega uma imagem do disco e retorna um objeto PIL."""
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    try:
        img = Image.open(file)
        img.load()  # força leitura completa — detecta corrupção aqui
        return img
    except UnidentifiedImageError:
        raise ValueError(f"Formato de imagem não reconhecido: {path}")
    except Exception as e:
        raise ValueError(f"Imagem corrompida ou inválida: {e}")


def validate_image(img: Image.Image) -> None:
    """Valida formato e dimensões. Lança ValueError se inválido."""
    fmt = img.format or ""
    if fmt.upper() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Formato '{fmt}' não suportado. Use: {', '.join(SUPPORTED_FORMATS)}"
        )
    w, h = img.size
    if w == 0 or h == 0:
        raise ValueError("Imagem com dimensões inválidas (largura ou altura = 0).")


def encode_image_bytes(img: Image.Image) -> bytes:
    """Converte PIL Image para bytes JPEG, redimensionando se necessário."""
    img = _resize_if_needed(img)
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG")
    return buffer.getvalue()


def encode_image_base64(img: Image.Image) -> str:
    """Converte PIL Image para string base64 (JPEG), pronto para envio à API."""
    return base64.b64encode(encode_image_bytes(img)).decode("utf-8")


def _resize_if_needed(img: Image.Image) -> Image.Image:
    w, h = img.size
    if w <= MAX_SIZE_PX and h <= MAX_SIZE_PX:
        return img
    img.thumbnail((MAX_SIZE_PX, MAX_SIZE_PX), Image.LANCZOS)
    return img
