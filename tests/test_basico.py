import pytest

import db
from coletar import corresponde
from fontes.base import Oferta
from unidades import extrair_quantidade, preco_por_unidade


@pytest.mark.parametrize("titulo, esperado", [
    ("Arroz Branco Tio João 5kg", (5.0, "kg")),
    ("Feijão Carioca Kicaldo 1 Kg", (1.0, "kg")),
    ("Leite Integral Tirol 1L", (1.0, "L")),
    ("Leite UHT Integral Piracanjuba 12x1L", (12.0, "L")),
    ("Café Melitta 500g", (0.5, "kg")),
    ("Iogurte 6 x 170ml", (pytest.approx(1.02), "L")),
    ("Óleo de Soja 900 ml", (pytest.approx(0.9), "L")),
    ("Feijão Cozido Vapza Caixa 500g 2 Unidades", (1.0, "kg")),
    ("Leite UHT Integral Tirol Caixa com Tampa 1l", (1.0, "L")),
])
def test_extrair_quantidade(titulo, esperado):
    assert extrair_quantidade(titulo) == esperado


def test_preco_por_unidade():
    assert preco_por_unidade(12.50, 500, "g") == 25.0


def _produto(**kw):
    base = {"termo_busca": "leite integral", "marca_preferida": None, "quantidade": 1, "unidade": "L"}
    return {**base, **kw}


def test_corresponde_filtra_titulo():
    assert corresponde(_produto(), "Leite Integral Tirol 1L")[0]
    assert not corresponde(_produto(), "Leite Desnatado Tirol 1L")[0]
    assert not corresponde(_produto(marca_preferida="Tirol"), "Leite Integral Piracanjuba 1L")[0]
    assert not corresponde(_produto(), "Leite em pó integral 400g")[0]


def test_banco(tmp_path):
    caminho = str(tmp_path / "t.db")
    db.inicializar(caminho)
    with db.conectar(caminho) as con:
        pid = db.adicionar_produto(con, "Arroz 5kg", "arroz 5kg", 5, "kg", preco_alvo=25)
        db.salvar_oferta(con, pid, Oferta("Giassi", "Arroz Tio João 5kg", 27.9, preco_original=31.9), 5.58, "kg")
        atuais = db.precos_atuais(con)
        assert atuais[0]["preco"] == 27.9
        db.remover_produto(con, pid)
        assert db.historico(con, pid) == []
