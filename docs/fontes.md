# Fontes de preço – como cada uma foi resolvida

CEP de referência: **89254-105** (Jaraguá do Sul). Configurável em `.env` (`RADAR_CEP`).

| Fonte | Status | Método |
|---|---|---|
| Giassi | ✅ etapa 2 | API VTEX pública (catálogo + simulação de carrinho) |
| Angeloni | ✅ etapa 3 | API VTEX pública (mesmo cliente do Giassi) |
| Cooper | ✅ etapa 3 | API VTEX pública, 2 lojas de Jaraguá |
| Mercado Livre | ⛔ bloqueado | API exige token; página de busca exige verificação de conta |
| Amazon | ✅ etapa 4 | Página de busca (HTML) |

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

## Amazon (`fontes/amazon.py`)

- Sem API pública de preços: lê `https://www.amazon.com.br/s?k=<termo>` com `httpx` + `selectolax`
  (`div[data-component-type="s-search-result"]`). Preço: `span.a-price:not(.a-text-price) .a-offscreen`;
  preço "de": `span.a-price[data-a-strike="true"] .a-offscreen` (a outra `a-text-price` é o R$/kg).
- Preço **nacional**, sem frete e sem relação com o CEP.
- Responde 503 com frequência (limite de acesso). Até 3 tentativas (pausas de 10 s e 20 s);
  se continuar, a busca falha no log e as demais seguem. Captcha → falha registrada, sem contorno.
- Títulos trazem kits: "(Embalagem com 5)", "Pack com 6 Unidades", "c/ 6UNID.", "3 x … 500g" são
  multiplicados. Vendedores às vezes anunciam errado ("Arroz 1kg, Pack com 30 Unidades" por R$ 20,20);
  por isso a coleta descarta R$/unidade abaixo da metade da mediana do produto (todas as lojas, 30 dias).

## Mercado Livre

- `api.mercadolibre.com/sites/MLB/search` → 403 `forbidden` sem token.
- `lista.mercadolivre.com.br/<termo>` → redireciona para `/gz/account-verification` (verificação anti-robô).
- Pelo CLAUDE.md não se contorna login/captcha. Alternativa legítima: API oficial com credenciais de um
  app cadastrado em developers.mercadolivre.com.br (não testado).

## Fontes extras em investigação

- **Fort Atacadista** (`www.fortatacadista.com.br`): plataforma "osuper" (GraphQL em
  `api.fortatacadista.com.br/graphql`, introspecção desativada). Loja de Jaraguá: `jaragua-sul`,
  `storeId 1627`. Para descobrir a consulta de busca que o próprio site usa, falta liberar
  `cdn.osuper.com.br` (JavaScript do site) e observar a requisição no navegador.
- **Komprão** (`komprao.com.br`, WordPress): tem loja em Jaraguá, mas sem loja online. As ofertas
  (`/ofertas/jaragua-do-sul/`) são um encarte no Issuu (imagens), desatualizado ("12 a 16/01"). Não incluído.
- **Condor**: `www.condor.com.br` e `condor.com.br` bloqueados no proxy; confirmar o domínio da loja online.
- **Rancho Bom** (`www.ranchobom.com.br`): site institucional, sem loja online nem API. Preços só nos
  tabloides (`/tabloides/<id>`), um "flipbook" de **imagens** – exigiria OCR, pouco confiável. As compras
  online são pelo app "Bem Bom" (apps fora do escopo). Não incluído por enquanto.
- Atacadão, Assaí, Carrefour e Breithaupt: descartados (sem loja física em Jaraguá do Sul).
