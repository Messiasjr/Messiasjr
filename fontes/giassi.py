"""Giassi – loja VTEX (www.giassi.com.br). Jaraguá do Sul é atendida pelo vendedor giassi15."""

from fontes.vtex import LojaVtex

NOME = "Giassi"
_loja = LojaVtex(NOME, "https://www.giassi.com.br")


def buscar(termo: str):
    return _loja.buscar(termo)
