"""Coleta diária: busca cada produto ativo em todas as fontes e grava no banco.

Rodar: python coletar.py
"""

import logging
import re
import statistics
import unicodedata

from dotenv import load_dotenv

import db
from fontes import FONTES
from unidades import extrair_quantidade, normalizar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("coleta.log", encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("coleta")
load_dotenv()


def _sem_acento(txt: str) -> str:
    return unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().lower()


def corresponde(produto, titulo: str) -> tuple[bool, float | None, str | None]:
    """Filtra pelo título: palavras do termo, marca preferida e tamanho compatível."""
    t = _sem_acento(titulo)
    palavras = [p for p in re.findall(r"[a-z]+", _sem_acento(produto["termo_busca"])) if len(p) > 2]
    if not all(p in t for p in palavras if p not in {"litro", "litros"}):
        return False, None, None
    if produto["marca_preferida"] and _sem_acento(produto["marca_preferida"]) not in t:
        return False, None, None
    encontrado = extrair_quantidade(titulo)
    if not encontrado:
        return False, None, None
    qtd_alvo, unidade_alvo = normalizar(produto["quantidade"], produto["unidade"])
    qtd, unidade = encontrado
    if unidade != unidade_alvo:
        return False, None, None
    # aceita embalagens de metade do tamanho até multipacks; comparação final é por R$/unidade
    if not (qtd_alvo * 0.5 <= qtd <= qtd_alvo * 12):
        return False, None, None
    return True, qtd, unidade


def descartar_implausiveis(aceitas: list, loja: str, referencia: list[float] = ()) -> list:
    """Remove R$/unidade abaixo da metade da mediana do produto (todas as lojas, últimos 30 dias,
    mais esta busca). Quase sempre é quantidade lida errada no título (ex.: "Arroz 1kg, Pack com
    30 Unidades" por R$ 20) e geraria falso "menor preço"."""
    valores = [pu for _, pu, _ in aceitas] + list(referencia)
    if len(valores) < 3:
        return aceitas
    piso = statistics.median(valores) / 2
    for oferta, pu, _ in aceitas:
        if pu < piso:
            log.warning("Implausível [%s]: %s (R$ %.2f/unid.)", loja, oferta.titulo, pu)
    return [a for a in aceitas if a[1] >= piso]


def coletar() -> None:
    db.inicializar()
    with db.conectar() as con:
        produtos = db.listar_produtos(con, somente_ativos=True)
    if not FONTES:
        log.warning("Nenhuma fonte registrada ainda.")
    for fonte in FONTES:
        for produto in produtos:
            try:
                ofertas = fonte.buscar(produto["termo_busca"])
            except Exception:
                log.exception("Falha em %s ao buscar '%s'", fonte.NOME, produto["termo_busca"])
                continue
            aceitas = []
            for oferta in ofertas:
                ok, qtd, unidade = corresponde(produto, oferta.titulo)
                if not ok:
                    log.debug("Descartado [%s]: %s", fonte.NOME, oferta.titulo)
                    continue
                aceitas.append((oferta, round(oferta.preco / qtd, 4), unidade))
            with db.conectar() as con:
                referencia = db.precos_unitarios_recentes(con, produto["id"])
                aceitas = descartar_implausiveis(aceitas, fonte.NOME, referencia)
                for oferta, preco_unitario, unidade in aceitas:
                    db.salvar_oferta(con, produto["id"], oferta, preco_unitario, unidade)
            log.info("%s | %s: %d resultados, %d aceitos", fonte.NOME, produto["nome"], len(ofertas), len(aceitas))


if __name__ == "__main__":
    coletar()
