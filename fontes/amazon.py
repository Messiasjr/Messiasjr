"""Amazon – página de busca (www.amazon.com.br/s?k=...), sem API pública de preços.

Preço nacional (não depende do CEP) e sem frete. Se a Amazon pedir captcha, a busca falha
e é registrada no log; não há tentativa de contornar.
"""

import logging
import re
import time

import httpx
from selectolax.lexbor import LexborHTMLParser

from fontes.base import USER_AGENT, Limitador, Oferta

log = logging.getLogger(__name__)

NOME = "Amazon"
BASE = "https://www.amazon.com.br"
_limitador = Limitador(3.0)
_cliente = httpx.Client(
    headers={"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"},
    timeout=30, follow_redirects=True,
)


def _valor(txt: str | None) -> float | None:
    """'R$ 1.234,56' -> 1234.56"""
    if not txt:
        return None
    m = re.search(r"[\d.]+,\d{2}", txt)
    return float(m.group().replace(".", "").replace(",", ".")) if m else None


def _pagina(termo: str) -> str:
    esperas = [10, 20]  # a Amazon responde 503 com frequência; tenta de novo com pausas maiores
    while True:
        _limitador.esperar()
        r = _cliente.get(BASE + "/s", params={"k": termo})
        if r.status_code == 503 and esperas:
            time.sleep(esperas.pop(0))
            continue
        r.raise_for_status()
        if "validateCaptcha" in r.text:
            raise RuntimeError("Amazon pediu captcha; busca ignorada")
        return r.text


def interpretar(html: str) -> list[Oferta]:
    ofertas, vistos = [], set()
    for res in LexborHTMLParser(html).css('div[data-component-type="s-search-result"]'):
        asin = res.attributes.get("data-asin")
        titulo = res.css_first("h2")
        preco = res.css_first("span.a-price:not(.a-text-price) span.a-offscreen")
        if not asin or asin in vistos or not titulo or not preco:
            continue
        vistos.add(asin)
        valor = _valor(preco.text())
        if valor is None:
            continue
        riscado = _valor(getattr(res.css_first('span.a-price[data-a-strike="true"] span.a-offscreen'), "text", lambda: None)())
        ofertas.append(Oferta(NOME, titulo.text(strip=True), valor, f"{BASE}/dp/{asin}",
                              riscado if riscado and riscado > valor else None))
    return ofertas


def buscar(termo: str) -> list[Oferta]:
    return interpretar(_pagina(termo))
