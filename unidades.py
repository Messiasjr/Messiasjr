"""Extração de tamanho/unidade de títulos e normalização de preço (R$/kg, R$/L, R$/un)."""

import re

# unidade base -> (unidade normalizada, fator para a base)
_FATORES = {
    "kg": ("kg", 1.0),
    "g": ("kg", 0.001),
    "mg": ("kg", 0.000001),
    "l": ("L", 1.0),
    "lt": ("L", 1.0),
    "litro": ("L", 1.0),
    "litros": ("L", 1.0),
    "ml": ("L", 0.001),
    "un": ("un", 1.0),
    "und": ("un", 1.0),
    "unid": ("un", 1.0),
    "unidades": ("un", 1.0),
}

_NUM = r"(\d+(?:[.,]\d+)?)"
_UNI = r"(kg|mg|g|ml|litros?|lt|l|unidades|unid|und|un)\b"
# "12x1L", "6 x 200ml", "c/12 1L" (multipack)
_RE_MULTI = re.compile(rf"(\d+)\s*(?:x|un\s*x|c/)\s*{_NUM}\s*{_UNI}", re.I)
_RE_SIMPLES = re.compile(rf"{_NUM}\s*{_UNI}", re.I)
# "N Unidades" depois do tamanho é ambíguo ("Arroz 1kg 8 Unidades" = 8 saquinhos dentro de 1kg;
# "Vapza 500g 2 Unidades" = 2 pacotes). Não é multiplicado: errar para cima evita falso "menor preço".


def _num(txt: str) -> float:
    return float(txt.replace(",", "."))


def extrair_quantidade(titulo: str) -> tuple[float, str] | None:
    """Retorna (quantidade, unidade base) a partir de um título. Ex.: 'Arroz 5kg' -> (5.0, 'kg')."""
    m = _RE_MULTI.search(titulo)
    if m:
        unidade, fator = _FATORES[m.group(3).lower()]
        return int(m.group(1)) * _num(m.group(2)) * fator, unidade
    m = _RE_SIMPLES.search(titulo)
    if m:
        unidade, fator = _FATORES[m.group(2).lower()]
        return _num(m.group(1)) * fator, unidade
    return None


def normalizar(quantidade: float, unidade: str) -> tuple[float, str]:
    """Converte uma quantidade cadastrada (ex.: 500, 'g') para a unidade base (0.5, 'kg')."""
    unidade_base, fator = _FATORES[unidade.lower()]
    return quantidade * fator, unidade_base


def preco_por_unidade(preco: float, quantidade: float, unidade: str) -> float | None:
    if not quantidade:
        return None
    qtd, _ = normalizar(quantidade, unidade)
    return round(preco / qtd, 4)
