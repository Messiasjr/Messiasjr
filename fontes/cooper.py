"""Cooper – loja VTEX (www.minhacooper.com.br).

O CEP devolve todas as lojas da rede; usa as duas de Jaraguá (Água Verde e Vila Nova).
"""

from fontes.vtex import LojaVtex

NOME = "Cooper"
_loja = LojaVtex(NOME, "https://www.minhacooper.com.br", filtro_vendedor="jaragua")


def buscar(termo: str):
    return _loja.buscar(termo)
