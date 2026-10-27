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
    ("Arroz Branco Tipo 1 Chinês Pacote 1kg 8 Unidades", (1.0, "kg")),
    ("Leite UHT Integral Tirol Caixa com Tampa 1l", (1.0, "L")),
    ("Camponesa Leite UHT Integral 1 L (Embalagem com 5)", (5.0, "L")),
    ("LEITE UHT NATURAL MILK ITAMBÉ INTEGRAL 1L c/ 6UNID.", (6.0, "L")),
    ("Arroz Parboilizado 1kg c/ 8 saquinhos", (1.0, "kg")),
    ("Leite Integral 1L - Caixa com 2 unidades", (2.0, "L")),
    ("3 x Feijão Carioca Orgânico 500g - Korin", (1.5, "kg")),
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


def test_amazon_interpretar():
    from fontes.amazon import interpretar
    html = """
    <div data-component-type="s-search-result" data-asin="B01">
      <h2><span>Leite Integral Betânia 1L</span></h2>
      <span class="a-price"><span class="a-offscreen">R$ 7,49</span></span>
      <span class="a-price a-text-price" data-a-strike="true"><span class="a-offscreen">R$ 7,89</span></span>
      <span class="a-price a-text-price"><span class="a-offscreen">R$ 7,49</span></span>
    </div>
    <div data-component-type="s-search-result" data-asin="B02">
      <h2><span>Arroz 5kg</span></h2>
      <span class="a-price"><span class="a-offscreen">R$ 1.034,99</span></span>
    </div>
    <div data-component-type="s-search-result" data-asin="B03"><h2>Sem preço</h2></div>
    """
    ofertas = interpretar(html)
    assert [(o.titulo, o.preco, o.preco_original) for o in ofertas] == [
        ("Leite Integral Betânia 1L", 7.49, 7.89),
        ("Arroz 5kg", 1034.99, None),
    ]
    assert ofertas[0].url == "https://www.amazon.com.br/dp/B01"


def test_descartar_implausiveis():
    from coletar import descartar_implausiveis
    def item(pu):
        return (Oferta("X", f"item {pu}", pu), pu, "kg")
    aceitas = [item(0.67), item(3.72), item(3.80), item(5.27)]
    assert [pu for _, pu, _ in descartar_implausiveis(aceitas, "X")] == [3.72, 3.80, 5.27]
    assert descartar_implausiveis(aceitas[:2], "X") == aceitas[:2]  # poucos itens: não filtra
    # loja só com itens caros não descarta o barato quando as outras lojas confirmam o preço
    caros = [item(8.23), item(25.8), item(45.7), item(46.7), item(113.9)]
    assert len(descartar_implausiveis(caros, "X", referencia=[7.99, 8.99, 9.79, 10.68])) == 5
