"""Angeloni – loja VTEX (super.angeloni.com.br). Jaraguá do Sul é atendida por superangeloni10."""

from fontes.vtex import LojaVtex

NOME = "Angeloni"
_loja = LojaVtex(NOME, "https://super.angeloni.com.br")


def buscar(termo: str):
    return _loja.buscar(termo)
