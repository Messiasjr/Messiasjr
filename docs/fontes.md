# Fontes de preço – como cada uma foi resolvida

| Fonte | Status | Método | Observações |
|---|---|---|---|
| Giassi | pendente (etapa 2) | — | Verificar API VTEX `/api/catalog_system/pub/products/search?ft=` |
| Angeloni | pendente (etapa 3) | — | Verificar API VTEX e seleção de loja por CEP 89250-000 |
| Cooper | pendente (etapa 3) | — | Verificar se a loja online atende Jaraguá do Sul |
| Mercado Livre | pendente (etapa 4) | — | Testar API `api.mercadolibre.com/sites/MLB/search` sem login |
| Amazon | pendente (etapa 4) | — | Página de busca `amazon.com.br/s?k=` |

> A investigação ("Antes de codar") ainda não foi feita: o ambiente de nuvem usado na
> etapa 1 bloqueia acesso a esses domínios.
