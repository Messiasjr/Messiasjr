# Fontes de preço – como cada uma foi resolvida

CEP de referência: **89254-105** (Jaraguá do Sul). Configurável em `.env` (`RADAR_CEP`).

| Fonte | Status | Método |
|---|---|---|
| Giassi | ✅ etapa 2 | API VTEX pública (catálogo + simulação de carrinho) |
| Angeloni | ✅ etapa 3 | API VTEX pública (mesmo cliente do Giassi) |
| Cooper | ✅ etapa 3 | API VTEX pública, 2 lojas de Jaraguá |
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

## Angeloni (`fontes/angeloni.py`)

- Loja de supermercado em `super.angeloni.com.br` (`www.angeloni.com.br/super/` redireciona para lá). VTEX.
- O CEP 89254-105 retorna um único vendedor: `superangeloni10` ("Angeloni Jaraguá do Sul").
- Mesmo fluxo do Giassi: catálogo para achar os SKUs, simulação de carrinho para o preço local.

## Cooper (`fontes/cooper.py`)

- Loja online em `www.minhacooper.com.br`. VTEX.
- O CEP devolve **todas** as 12 lojas da rede (Blumenau, Indaial, Timbó, Joinville…). A fonte
  filtra as de Jaraguá: `minhacoopersuperaguaverdejaragua` e `minhacoopersupervilanovajaragua`.
- Os preços foram iguais nas duas, mas a disponibilidade muda (item "sem estoque" numa e
  disponível na outra). A coleta simula nas duas e guarda o menor preço disponível de cada SKU.

## Unidades nos títulos

- "N Unidades" depois do tamanho é ambíguo: "Arroz Chinês Pacote 1kg 8 Unidades" (R$ 4,99) são
  8 saquinhos dentro de 1 kg, já "Vapza 500g 2 Unidades" são 2 pacotes. Não é multiplicado.

## Observações preliminares das demais (a confirmar na etapa 4)

- Mercado Livre: `api.mercadolibre.com/sites/MLB/search` respondeu 403 sem login → usar página de busca.
- Amazon: página de busca respondeu 503 para o User-Agent do robô.
