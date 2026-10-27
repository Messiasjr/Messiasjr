# Projeto: Radar de Preços – Jaraguá do Sul

## Objetivo
Lista de compras inteligente. Eu cadastro produtos (ex.: leite integral 1L, arroz 5kg, feijão carioca 1kg). O programa consulta periodicamente os mercados, guarda o histórico de preços e me avisa quando um produto está em promoção ou com o menor preço.

## Fontes (fase 1)
- Giassi (site/loja online)
- Angeloni (site/loja online)
- Cooper (site/loja online)
- Mercado Livre
- Amazon

Fora do escopo: aplicativos de celular e redes sociais.

## Antes de codar
1. Abra cada site, faça uma busca manual (ex.: "leite integral") e inspecione as requisições de rede.
2. Se o site tiver API JSON pública (por exemplo, o padrão VTEX `/api/catalog_system/pub/products/search?ft=...`), use-a em vez de raspar HTML.
3. Para o Mercado Livre, verifique se a API oficial de busca funciona sem login. Se não funcionar, use a página de busca.
4. Confirme o CEP/loja de Jaraguá do Sul (CEP 89250-000) quando o preço depender da região.
5. Documente em `docs/fontes.md` como cada fonte foi resolvida.

## Stack
- Python 3.11+
- SQLite (arquivo local `radar.db`)
- Streamlit para a interface: cadastrar produtos, ver preços atuais e histórico
- `httpx` + `selectolax`. Use Playwright só se algum site exigir JavaScript.
- Agendamento: script `coletar.py` rodado 1x por dia (Agendador de Tarefas do Windows / cron)
- Notificação: Telegram bot (token e chat_id em `.env`). Deixe o canal de notificação plugável para trocar por e-mail depois.

## Modelo de dados
- `produtos`: id, nome, termo_busca, marca_preferida (opcional), unidade/tamanho, preco_alvo (opcional), ativo
- `ofertas`: id, produto_id, loja, titulo_encontrado, preco, preco_original (se houver), url, coletado_em
- Normalize o preço por unidade (R$/L, R$/kg) para comparar embalagens diferentes.

## Regras de "promoção" (avisar quando)
- O preço caiu ≥ 10% em relação à média dos últimos 30 dias, OU
- O site marca o item como oferta (existe preço "de/por"), OU
- O preço ficou abaixo do `preco_alvo` cadastrado.
- Resumo semanal (segunda-feira): o mercado mais barato para cada item e o total da lista em cada mercado.

## Qualidade da coleta
- Para cada busca, filtre os resultados pelo título (marca/tamanho) e descarte itens que não correspondem. Guarde o título encontrado para eu conferir.
- Cada loja tem seu próprio módulo em `fontes/` com interface comum `buscar(termo) -> list[Oferta]`.
- Respeite os sites: no máximo 1 requisição a cada 2–3 s por site, User-Agent identificado, sem burlar login ou captcha.
- Se uma fonte falhar, registre no log e siga com as demais.

## Entregas por etapa
1. Estrutura do projeto + banco + interface Streamlit de cadastro
2. Fonte Giassi funcionando com teste real (3 produtos)
3. Angeloni e Cooper
4. Mercado Livre e Amazon
5. Regras de promoção + Telegram + resumo semanal
6. README com instruções de instalação e agendamento no Windows

Ao fim de cada etapa, rode e mostre o resultado real antes de seguir.
