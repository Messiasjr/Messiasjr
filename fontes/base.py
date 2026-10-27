"""Interface comum das fontes: cada módulo em fontes/ expõe `buscar(termo) -> list[Oferta]`."""

import time
from dataclasses import dataclass

USER_AGENT = "RadarPrecosJaragua/0.1 (uso pessoal; lista de compras)"


@dataclass
class Oferta:
    loja: str
    titulo: str
    preco: float
    url: str | None = None
    preco_original: float | None = None  # preço "de" quando o site marca promoção

    @property
    def em_oferta(self) -> bool:
        return self.preco_original is not None and self.preco_original > self.preco


class Limitador:
    """Garante intervalo mínimo entre requisições ao mesmo site."""

    def __init__(self, intervalo_s: float = 2.5):
        self.intervalo_s = intervalo_s
        self._ultimo = 0.0

    def esperar(self) -> None:
        falta = self.intervalo_s - (time.monotonic() - self._ultimo)
        if falta > 0:
            time.sleep(falta)
        self._ultimo = time.monotonic()
