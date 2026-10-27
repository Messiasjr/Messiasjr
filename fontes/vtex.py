"""Cliente genérico para lojas VTEX (catálogo público + simulação de carrinho regionalizada).

O catálogo (`/api/catalog_system/pub/products/search`) devolve o preço do vendedor padrão,
que pode diferir da loja física que atende o CEP. Por isso o preço final vem de
`/api/checkout/pub/orderForms/simulation` com o vendedor da região do CEP.
"""

import logging
import os
from urllib.parse import quote, urlencode

import httpx

from fontes.base import USER_AGENT, Limitador, Oferta

log = logging.getLogger(__name__)

CEP_PADRAO = "89254105"  # Jaraguá do Sul


def cep() -> str:
    return os.environ.get("RADAR_CEP", CEP_PADRAO).replace("-", "").replace(".", "")


class LojaVtex:
    def __init__(self, nome: str, base_url: str, max_resultados: int = 20, sc: int = 1):
        self.nome = nome
        self.base_url = base_url.rstrip("/")
        self.max_resultados = max_resultados
        self.sc = sc
        self.limitador = Limitador()
        self._vendedor: str | None = None
        self._cliente = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)

    def _get(self, caminho: str, **params):
        self.limitador.esperar()
        # o firewall de algumas lojas rejeita "+" como espaço; usa %20
        r = self._cliente.get(f"{self.base_url}{caminho}?{urlencode(params, quote_via=quote)}")
        r.raise_for_status()
        return r.json()

    def _post(self, caminho: str, corpo: dict, **params):
        self.limitador.esperar()
        r = self._cliente.post(self.base_url + caminho, json=corpo, params=params)
        r.raise_for_status()
        return r.json()

    def vendedor_regional(self) -> str | None:
        """Vendedor (loja física) que atende o CEP configurado."""
        if self._vendedor is None:
            regioes = self._get("/api/checkout/pub/regions", country="BRA", postalCode=cep())
            vendedores = regioes[0]["sellers"] if regioes else []
            if not vendedores:
                raise RuntimeError(f"{self.nome}: nenhuma loja atende o CEP {cep()}")
            self._vendedor = vendedores[0]["id"]
            log.info("%s: CEP %s atendido por %s", self.nome, cep(), self._vendedor)
        return self._vendedor

    def buscar(self, termo: str) -> list[Oferta]:
        produtos = self._get(
            "/api/catalog_system/pub/products/search",
            ft=termo, _from=0, _to=self.max_resultados - 1, sc=self.sc,
        )
        itens = {}
        for p in produtos:
            if p.get("items"):
                sku = p["items"][0]["itemId"]
                itens[sku] = (p["productName"], p.get("link"))
        if not itens:
            return []

        vendedor = self.vendedor_regional()
        simulacao = self._post(
            "/api/checkout/pub/orderForms/simulation",
            {"items": [{"id": sku, "quantity": 1, "seller": vendedor} for sku in itens],
             "postalCode": cep(), "country": "BRA"},
            sc=self.sc,
        )
        ofertas = []
        for item in simulacao.get("items", []):
            if item.get("availability") != "available" or item["id"] not in itens:
                continue
            titulo, url = itens[item["id"]]
            preco = (item.get("sellingPrice") or item["price"]) / 100
            de = (item.get("listPrice") or 0) / 100
            ofertas.append(Oferta(self.nome, titulo, preco, url, de if de > preco else None))
        return ofertas
