import json
import re
from typing import Optional


def parse_menu_response(raw_text: str) -> list[dict]:
    """Converte texto bruto da LLM em lista de {'produto': str, 'preco': str}."""
    text = raw_text.strip()

    result = _try_parse_json(text)
    if result is not None:
        return result

    if "|" in text:
        result = _parse_markdown_table(text)
        if result:
            return result

    return _parse_plain_text(text)


# --- estratégias de parsing --------------------------------------------------

def _try_parse_json(text: str) -> Optional[list[dict]]:
    # extrai bloco ```json ... ``` se houver
    match = re.search(r"```(?:json)?\s*([\[{].*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # procura array ou objeto JSON em qualquer posição do texto
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None

    if isinstance(data, list):
        return [_normalize_item(item) for item in data if isinstance(item, dict)]

    # tenta extrair lista de dentro de um objeto {"items": [...]}
    for key in ("items", "cardapio", "menu", "produtos"):
        if key in data and isinstance(data[key], list):
            return [_normalize_item(item) for item in data[key] if isinstance(item, dict)]

    return None


def _parse_markdown_table(text: str) -> list[dict]:
    items = []
    header_passed = False

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue

        # linha separadora: |---|---|
        if re.match(r"^\|[\s\-:]+\|", line):
            header_passed = True
            continue

        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2:
            continue

        produto, preco = cols[0], cols[1]

        # pula cabeçalho se separador ainda não apareceu
        if not header_passed and re.search(r"produto|item|name", produto, re.IGNORECASE):
            continue

        if produto and preco:
            items.append({"produto": produto, "preco": normalize_price(preco)})

    return items


def _parse_plain_text(text: str) -> list[dict]:
    items = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # aceita " - " (com espaços) ou ": " — evita quebrar nomes com hífen
        match = re.match(r"^(.+?)\s+-\s+(.+)$", line) or re.match(r"^(.+?):\s+(.+)$", line)
        if not match:
            continue

        produto = match.group(1).strip()
        preco_raw = match.group(2).strip()

        if produto and preco_raw:
            items.append({"produto": produto, "preco": normalize_price(preco_raw)})

    return items


# --- normalização de preço ---------------------------------------------------

def normalize_price(raw: str) -> str:
    """Normaliza qualquer formato de preço para 'R$ XX,XX'."""
    cleaned = raw.strip()

    if cleaned.upper() in ("N/D", "ND", "-", ""):
        return "N/D"

    # remove símbolo de moeda
    cleaned = re.sub(r"R\$\s*", "", cleaned).strip()

    # detecta e converte separadores
    if re.search(r"\.\d{3}", cleaned) and "," in cleaned:
        # formato BR com milhar: 1.234,56
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif re.search(r",\d{3}", cleaned) and "." in cleaned:
        # formato EN com milhar: 1,234.56
        cleaned = cleaned.replace(",", "")
    else:
        # simples: 25,00 ou 25.00 ou 25
        cleaned = cleaned.replace(",", ".")

    try:
        value = float(cleaned)
        # formata em BR: R$ 1.234,56
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except ValueError:
        return raw.strip()


def _normalize_item(item: dict) -> dict:
    """Normaliza chaves de um dict JSON para {produto, preco}."""
    produto = (
        item.get("produto")
        or item.get("product")
        or item.get("name")
        or item.get("nome")
        or item.get("item")
        or ""
    )
    preco = (
        item.get("preco")
        or item.get("price")
        or item.get("valor")
        or item.get("preco")
        or ""
    )
    return {"produto": str(produto).strip(), "preco": normalize_price(str(preco))}
