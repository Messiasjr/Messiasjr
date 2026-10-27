# Fontes de preço – como cada uma foi resolvida

CEP de referência: **89254-105** (Jaraguá do Sul). Configurável em `.env` (`RADAR_CEP`).

| Fonte | Status | Método |
|---|---|---|
| Giassi | ✅ etapa 2 | API VTEX pública (catálogo + simulação de carrinho) |
| Angeloni | pendente (etapa 3) | — |
| Cooper | pendente (etapa 3) | — |
| Mercado Livre | pendente (etapa 4) | — |
| Amazon | pendente (etapa 4) | — |

## Giassi (`fontes/giassi.py`, via `fontes/vtex.py`)

- Loja VTEX. A busca usa `GET /api/catalog_system/pub/products/search?ft=<termo>&_from=0&_to=19&sc=1`.
- **Preço depende da região.** `GET /api/checkout/pub/regions?country=BRA&postalCode=89254105`
  retorna o vendedor `giassi15` (loja de Jaraguá). Outros CEPs: Joinville → `giassi08`,
  Florianópolis → `giassi07`. O CEP genérico 89250-000 não é atendido por nenhuma loja.
- O catálogo devolve o preço do vendedor padrão (`1`), que pode diferir da loja local
  (ex.: Leite em Pó Ninho 575g: R$ 40,90 no catálogo, R$ 39,68 na giassi15). Por isso o preço
  final vem de `POST /api/checkout/pub/orderForms/simulation?sc=1` com `seller=giassi15` e o CEP.
  Usa `sellingPrice` como preço e `listPrice` como preço "de" quando maior.
- Itens com `availability != "available"` são descartados.
- O firewall do site responde 400 ("Scripts are not allowed") quando o espaço na URL vem como
  `+`; a query string é montada com `%20`.
- 1 requisição a cada 2,5 s; 3 requisições por produto (a de região só na primeira busca).

## Observações preliminares das demais (a confirmar nas etapas 3–4)

- Angeloni: `www.angeloni.com.br/super/` redireciona para `super.angeloni.com.br` (liberar esse domínio).
- Cooper: `coopershop.com.br` não respondeu (erro 502 no proxy) – confirmar o domínio da loja online.
- Mercado Livre: `api.mercadolibre.com/sites/MLB/search` respondeu 403 sem login → usar página de busca.
- Amazon: página de busca respondeu 503 para o User-Agent do robô.
