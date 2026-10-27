"""Registro das fontes de preço. Cada fonte é um módulo com `NOME` e `buscar(termo)`."""

from fontes import angeloni, cooper, giassi

# Próximas: Mercado Livre e Amazon (etapa 4).
FONTES = [giassi, angeloni, cooper]
