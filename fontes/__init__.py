"""Registro das fontes de preço. Cada fonte é um módulo com `NOME` e `buscar(termo)`."""

from fontes import amazon, angeloni, cooper, giassi

FONTES = [giassi, angeloni, cooper, amazon]
