"""Interface Streamlit: cadastro de produtos, preços atuais e histórico.

Rodar: streamlit run app.py
"""

import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

import db

PASTA = Path(__file__).resolve().parent
TRAVA = PASTA / ".coleta.lock"

UNIDADES = ["kg", "g", "L", "ml", "un"]

st.set_page_config(page_title="Radar de Preços – Jaraguá do Sul", page_icon="🛒", layout="wide")
db.inicializar()

st.title("🛒 Radar de Preços – Jaraguá do Sul")


def coleta_em_andamento() -> bool:
    # trava com mais de 30 min é de uma coleta interrompida
    return TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 30 * 60


with st.sidebar:
    st.header("Coleta de preços")
    st.caption("Consulta todas as lojas para os produtos ativos. Leva ~1 min por produto.")
    if st.button("🔄 Coletar preços agora", type="primary", disabled=coleta_em_andamento()):
        TRAVA.touch()
        try:
            with st.status("Coletando preços…", expanded=True) as status:
                processo = subprocess.Popen(
                    [sys.executable, "coletar.py"], cwd=PASTA, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                )
                for linha in processo.stdout:
                    # mostra só o resumo de cada busca e as falhas, não cada requisição HTTP
                    partes = linha.split(" ", 3)  # data, hora, nível, mensagem
                    if len(partes) < 4 or partes[2] not in {"INFO", "WARNING", "ERROR"}:
                        continue
                    if partes[2] != "INFO":
                        st.text("⚠️ " + partes[3].strip())
                    elif " | " in partes[3]:
                        st.text(partes[3].strip())
                ok = processo.wait() == 0
                status.update(label="Coleta concluída" if ok else "Coleta terminou com erro",
                              state="complete" if ok else "error")
        finally:
            TRAVA.unlink(missing_ok=True)
    elif coleta_em_andamento():
        st.info("Já há uma coleta em andamento.")
aba_produtos, aba_precos, aba_historico = st.tabs(["Produtos", "Preços atuais", "Histórico"])

# ---------------- Produtos ----------------
with aba_produtos:
    st.subheader("Cadastrar produto")
    with st.form("novo_produto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome", placeholder="Leite integral 1L")
        termo = c2.text_input("Termo de busca", placeholder="leite integral 1l")
        c3, c4, c5, c6 = st.columns(4)
        quantidade = c3.number_input("Tamanho", min_value=0.0, value=1.0, step=0.5)
        unidade = c4.selectbox("Unidade", UNIDADES, index=2)
        marca = c5.text_input("Marca preferida (opcional)")
        preco_alvo = c6.number_input("Preço-alvo R$ (opcional)", min_value=0.0, value=0.0, step=0.10)
        if st.form_submit_button("Adicionar"):
            if not nome.strip() or not termo.strip() or quantidade <= 0:
                st.error("Preencha nome, termo de busca e tamanho.")
            else:
                with db.conectar() as con:
                    db.adicionar_produto(con, nome, termo, quantidade, unidade, marca, preco_alvo or None)
                st.success(f"'{nome}' cadastrado.")

    st.subheader("Minha lista")
    with db.conectar() as con:
        produtos = [dict(p) for p in db.listar_produtos(con)]

    if not produtos:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        df = pd.DataFrame(produtos).set_index("id")
        df["ativo"] = df["ativo"].astype(bool)
        editado = st.data_editor(
            df,
            column_config={
                "nome": "Nome",
                "termo_busca": "Termo de busca",
                "marca_preferida": "Marca preferida",
                "quantidade": st.column_config.NumberColumn("Tamanho", min_value=0.0),
                "unidade": st.column_config.SelectboxColumn("Unidade", options=UNIDADES, required=True),
                "preco_alvo": st.column_config.NumberColumn("Preço-alvo", format="R$ %.2f"),
                "ativo": "Ativo",
            },
            key="editor_produtos",
        )
        c1, c2 = st.columns([1, 3])
        if c1.button("Salvar alterações"):
            with db.conectar() as con:
                for pid, linha in editado.iterrows():
                    campos = linha.to_dict()
                    campos["ativo"] = int(bool(campos["ativo"]))
                    campos = {k: (None if pd.isna(v) else v) for k, v in campos.items()}
                    db.atualizar_produto(con, int(pid), **campos)
            st.success("Alterações salvas.")
            st.rerun()

        with c2.popover("Remover produto"):
            opcoes = {f"{p['nome']} (#{p['id']})": p["id"] for p in produtos}
            alvo = st.selectbox("Produto", list(opcoes), key="remover_produto")
            if st.button("Remover (apaga também o histórico)", type="primary"):
                with db.conectar() as con:
                    db.remover_produto(con, opcoes[alvo])
                st.rerun()

# ---------------- Preços atuais ----------------
with aba_precos:
    todas = st.toggle("Mostrar todas as opções encontradas (não só a mais barata por loja)")
    with db.conectar() as con:
        atuais = [dict(r) for r in db.precos_atuais(con, todas=todas)]
    if not atuais:
        st.info("Ainda não há preços coletados. Rode `python coletar.py`.")
    else:
        df = pd.DataFrame(atuais)
        df["oferta"] = df["preco_original"].notna() & (df["preco_original"] > df["preco"])
        st.dataframe(
            df,
            column_config={
                "produto": "Produto",
                "loja": "Loja",
                "titulo_encontrado": "Título encontrado",
                "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                "preco_original": st.column_config.NumberColumn("De", format="R$ %.2f"),
                "preco_unitario": st.column_config.NumberColumn("R$/unid.", format="R$ %.2f"),
                "unidade_base": "Unid.",
                "url": st.column_config.LinkColumn("Link", display_text="abrir"),
                "coletado_em": "Coletado em",
                "oferta": "Oferta?",
            },
            hide_index=True,
        )

# ---------------- Histórico ----------------
with aba_historico:
    with db.conectar() as con:
        produtos = db.listar_produtos(con)
    if not produtos:
        st.info("Cadastre produtos primeiro.")
    else:
        mapa = {f"{p['nome']} (#{p['id']})": p["id"] for p in produtos}
        escolhido = st.selectbox("Produto", list(mapa), key="historico_produto")
        with db.conectar() as con:
            hist = [dict(r) for r in db.historico(con, mapa[escolhido])]
        if not hist:
            st.info("Sem histórico para este produto.")
        else:
            df = pd.DataFrame(hist)
            df["coletado_em"] = pd.to_datetime(df["coletado_em"])
            grafico = df.pivot_table(index="coletado_em", columns="loja", values="preco_unitario", aggfunc="min")
            st.line_chart(grafico)
            st.dataframe(df.sort_values("coletado_em", ascending=False), hide_index=True)
