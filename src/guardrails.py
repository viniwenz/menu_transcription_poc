import logging
import re
from dataclasses import dataclass, field

from src.parser import parse_menu_response

logger = logging.getLogger(__name__)

RETRY_PROMPT = """A resposta anterior não estava no formato correto ou estava incompleta.
Analise a imagem novamente com cuidado e retorne SOMENTE a tabela markdown abaixo, sem texto adicional:

| Produto | Preço |
|---------|-------|
| Nome exato do item | R$ XX,XX |

Regras obrigatórias:
- Inclua TODOS os itens visíveis no cardápio
- Se não souber o preço de um item, use N/D
- Não adicione explicações, apenas a tabela
"""


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


def validate_menu(items: list[dict]) -> ValidationResult:
    """Valida lista de itens extraídos do cardápio."""
    errors = []

    if not items:
        errors.append("Nenhum produto foi extraído.")
        return ValidationResult(valid=False, errors=errors)

    for i, item in enumerate(items, start=1):
        if not item.get("produto", "").strip():
            errors.append(f"Item {i}: nome do produto está vazio.")

        preco = item.get("preco", "")
        if not _is_valid_price(preco):
            errors.append(f"Item {i} ('{item.get('produto')}'): preço '{preco}' inválido.")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def transcribe_with_retry(image_bytes: bytes, client, max_attempts: int = 2) -> list[dict]:
    """Transcreve cardápio com retry automático se a validação falhar."""
    last_errors: list[str] = []

    for attempt in range(1, max_attempts + 1):
        prompt_override = RETRY_PROMPT if attempt > 1 else None
        logger.info("Tentativa %d/%d", attempt, max_attempts)

        try:
            raw = client.transcribe_menu(image_bytes, prompt_override=prompt_override)
            items = parse_menu_response(raw)
            result = validate_menu(items)

            if result.valid:
                if attempt > 1:
                    logger.info("Sucesso na tentativa %d.", attempt)
                return items

            last_errors = result.errors
            logger.warning("Tentativa %d falhou: %s", attempt, result.errors)

        except Exception as e:
            last_errors = [str(e)]
            logger.error("Tentativa %d erro: %s", attempt, e)

    raise ValueError(f"Falha após {max_attempts} tentativas. Erros: {last_errors}")


def _is_valid_price(preco: str) -> bool:
    if preco == "N/D":
        return True
    return bool(re.match(r"^R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}$", preco))
