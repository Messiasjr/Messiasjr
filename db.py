"""Acesso ao SQLite (radar.db): produtos e ofertas."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from fontes.base import Oferta

SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    termo_busca     TEXT NOT NULL,
    marca_preferida TEXT,
    quantidade      REAL NOT NULL,          -- ex.: 1, 5, 500
    unidade         TEXT NOT NULL,          -- kg, g, L, ml, un
    preco_alvo      REAL,
    ativo           INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ofertas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id        INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    loja              TEXT NOT NULL,
    titulo_encontrado TEXT NOT NULL,
    preco             REAL NOT NULL,
    preco_original    REAL,
    preco_unitario    REAL,                 -- R$/kg, R$/L ou R$/un
    unidade_base      TEXT,
    url               TEXT,
    coletado_em       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_ofertas_produto_data ON ofertas(produto_id, coletado_em);
"""


def caminho_db() -> str:
    return os.environ.get("RADAR_DB", "radar.db")


@contextmanager
def conectar(caminho: str | None = None):
    con = sqlite3.connect(caminho or caminho_db())
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def inicializar(caminho: str | None = None) -> None:
    with conectar(caminho) as con:
        con.executescript(SCHEMA)


# ---------- produtos ----------

def adicionar_produto(con, nome, termo_busca, quantidade, unidade,
                      marca_preferida=None, preco_alvo=None) -> int:
    cur = con.execute(
        "INSERT INTO produtos (nome, termo_busca, marca_preferida, quantidade, unidade, preco_alvo)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (nome.strip(), termo_busca.strip(), (marca_preferida or "").strip() or None,
         quantidade, unidade, preco_alvo or None),
    )
    return cur.lastrowid


def atualizar_produto(con, produto_id, **campos) -> None:
    permitidos = {"nome", "termo_busca", "marca_preferida", "quantidade", "unidade", "preco_alvo", "ativo"}
    campos = {k: v for k, v in campos.items() if k in permitidos}
    if not campos:
        return
    sets = ", ".join(f"{k} = ?" for k in campos)
    con.execute(f"UPDATE produtos SET {sets} WHERE id = ?", (*campos.values(), produto_id))


def remover_produto(con, produto_id) -> None:
    con.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def listar_produtos(con, somente_ativos=False) -> list[sqlite3.Row]:
    sql = "SELECT * FROM produtos"
    if somente_ativos:
        sql += " WHERE ativo = 1"
    return con.execute(sql + " ORDER BY nome").fetchall()


# ---------- ofertas ----------

def salvar_oferta(con, produto_id: int, oferta: Oferta, preco_unitario=None,
                  unidade_base=None, coletado_em: str | None = None) -> int:
    cur = con.execute(
        "INSERT INTO ofertas (produto_id, loja, titulo_encontrado, preco, preco_original,"
        " preco_unitario, unidade_base, url, coletado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (produto_id, oferta.loja, oferta.titulo, oferta.preco, oferta.preco_original,
         preco_unitario, unidade_base, oferta.url,
         coletado_em or datetime.now().isoformat(timespec="seconds")),
    )
    return cur.lastrowid


def precos_atuais(con, todas=False) -> list[sqlite3.Row]:
    """Ofertas do dia da última coleta de cada (produto, loja).

    Por padrão só a mais barata por R$/unidade; com `todas=True`, todas as aceitas.
    """
    return con.execute(f"""
        WITH ultima AS (
            SELECT o.*, ROW_NUMBER() OVER (
                       PARTITION BY o.produto_id, o.loja ORDER BY o.preco_unitario, o.preco) AS ordem
            FROM ofertas o
            WHERE date(o.coletado_em) = (
                SELECT MAX(date(x.coletado_em)) FROM ofertas x
                WHERE x.produto_id = o.produto_id AND x.loja = o.loja)
        )
        SELECT p.nome AS produto, u.loja, u.titulo_encontrado, u.preco, u.preco_original,
               u.preco_unitario, u.unidade_base, u.url, u.coletado_em
        FROM ultima u
        JOIN produtos p ON p.id = u.produto_id
        {"" if todas else "WHERE u.ordem = 1"}
        ORDER BY p.nome, u.preco_unitario
    """).fetchall()


def historico(con, produto_id: int) -> list[sqlite3.Row]:
    return con.execute(
        "SELECT loja, preco, preco_original, preco_unitario, titulo_encontrado, url, coletado_em"
        " FROM ofertas WHERE produto_id = ? ORDER BY coletado_em",
        (produto_id,),
    ).fetchall()
