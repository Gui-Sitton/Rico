import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from pathlib import Path

# 🧩 IMPORTAR SUPABASE FUNÇÕES
from supabase_utils import (
    carregar_clientes,
    carregar_vendas,
    carregar_itens_venda,
    carregar_produtos,
    carregar_movfinanceiro,
    carregar_plantacoes,restore_from_cookie
)

# ===============================
# 🔧 FUNÇÕES DE RELATÓRIO
# ===============================

import pandas as pd
import plotly.express as px
import base64
from io import BytesIO
restore_from_cookie()
def gerar_relatorio_vendas(periodo_inicio=None, periodo_fim=None):
    # --- Carrega dados do Supabase ---------------------------------
    vendas_df    = carregar_vendas()          # venda_id, cliente_id, data_venda, valor_venda
    itens_df     = carregar_itens_venda()     # item_venda_id, venda_id, produto_id, quantidade, valor_unitario
    produtos_df  = carregar_produtos()        # produto_id, Produto
    plantacoes_df = carregar_plantacoes()     # cliente_id, Estado, ...

    # ---------------------------------------------------------------
    # === PRÉ‑PROCESSAMENTO ===
    vendas_df["data_venda"] = pd.to_datetime(vendas_df["data_venda"], errors="coerce")

    def _valor_brasileiro_para_float(valor_str):
        try:
            return float(valor_str.replace(".", "").replace(",", "."))
        except Exception:
            return None

    vendas_df["valor_venda"] = vendas_df["valor_venda"].apply(_valor_brasileiro_para_float)

    # --- Filtros opcionais
    if periodo_inicio:
        vendas_df = vendas_df[vendas_df["data_venda"] >= pd.to_datetime(periodo_inicio)]
    if periodo_fim:
        vendas_df = vendas_df[vendas_df["data_venda"] <= pd.to_datetime(periodo_fim)]

    # ---------------------------------------------------------------
    # === KPIs ===
    hoje               = pd.Timestamp.today()
    doze_meses_atras   = hoje - pd.DateOffset(months=12)

    faturamento_total  = vendas_df["valor_venda"].sum()
    faturamento_12m    = vendas_df[vendas_df["data_venda"] >= doze_meses_atras]["valor_venda"].sum()
    regioes_ativas     = plantacoes_df["Estado"].dropna().nunique()

    # ---------------------------------------------------------------
    # === PRODUTOS (qtd e faturamento) ===
    itens_df["faturamento"] = itens_df["quantidade"] * itens_df["valor_unitario"]

    qtd_por_produto = (
        itens_df.groupby("produto_id")["quantidade"]
        .sum()
        .reset_index()
        .merge(produtos_df, on="produto_id", how="left")
        .sort_values("quantidade", ascending=False)
    )

    faturamento_produto = (
        itens_df.groupby("produto_id")["faturamento"]
        .sum()
        .reset_index()
        .merge(produtos_df, on="produto_id", how="left")
        .sort_values("faturamento", ascending=False)
    )

    # ---------------------------------------------------------------
    # === Faturamento por Estado ===
    vendas_plantacoes = vendas_df.merge(
        plantacoes_df[["cliente_id", "Estado"]], on="cliente_id", how="left"
    )
    faturamento_estado = (
        vendas_plantacoes.dropna(subset=["Estado"])
        .groupby("Estado")["valor_venda"]
        .sum()
        .reset_index()
    )

    fig = px.pie(
        faturamento_estado,
        names="Estado",
        values="valor_venda",
        title="Faturamento Total por Estado",
        color_discrete_sequence=px.colors.sequential.Viridis_r,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")

    # --- Converte o gráfico em PNG base64 para embutir no e‑mail ---
    buf = BytesIO()
    fig.write_image(buf, format="png")   # requer kaleido
    img_base64 = base64.b64encode(buf.getvalue()).decode()

    # ===============================================================
    # === HTML FINAL (dashboard compacto) ===
    def brl(x):  # formatação em Real brasileiro
        return f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    kpi_html = f"""
    <div style="display:flex;justify-content:space-around;text-align:center;font-family:Arial;margin-bottom:15px">
        <div style="flex:1;padding:10px;border:1px solid #ddd;border-radius:8px">
            <h3>💰 Faturamento Total</h3>
            <h2>{brl(faturamento_total)}</h2>
        </div>
        <div style="flex:1;padding:10px;border:1px solid #ddd;border-radius:8px">
            <h3>📅 Últimos 12&nbsp;meses</h3>
            <h2>{brl(faturamento_12m)}</h2>
        </div>
        <div style="flex:1;padding:10px;border:1px solid #ddd;border-radius:8px">
            <h3>📍 Regiões Ativas</h3>
            <h2>{regioes_ativas}</h2>
        </div>
    </div>
    """

    html = (
        "<h1>Relatório de Vendas</h1>"
        + kpi_html
        + "<h2>📊 Faturamento por Estado</h2>"
        + f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%"/>'
        + "<h2>🧮 Quantidade por Produto</h2>"
        + qtd_por_produto[["Produto", "quantidade"]]
            .rename(columns={"quantidade": "Quantidade"})
            .to_html(index=False, border=0)
        + "<h2>💵 Faturamento por Produto</h2>"
        + faturamento_produto.assign(
            faturamento=lambda df: df["faturamento"].apply(brl)
          )[["Produto", "faturamento"]]
            .rename(columns={"faturamento": "Faturamento"})
            .to_html(index=False, border=0)
    )

    return {"html": html}


def gerar_relatorio_financeiro(periodo_inicio=None, periodo_fim=None):
    mov = carregar_movfinanceiro()
    mov["Data"] = pd.to_datetime(mov["Data"])
    if periodo_inicio:
        mov = mov[mov["Data"] >= pd.to_datetime(periodo_inicio)]
    if periodo_fim:
        mov = mov[mov["Data"] <= pd.to_datetime(periodo_fim)]

    mov["Mês"] = mov["Data"].dt.to_period("M")
    fluxo = mov.groupby("Mês").agg(
        Entrada_Caixa=("Entrada Caixa", "sum"),
        Saida_Caixa=("Saída Caixa", "sum"),
        Entrada_Banco=("Entrada Banco", "sum"),
        Saida_Banco=("Saída Banco", "sum"),
    ).reset_index()
    fluxo["Fluxo_Caixa (R$)"] = fluxo["Entrada_Caixa"] - fluxo["Saida_Caixa"]
    fluxo["Fluxo_Banco (R$)"] = fluxo["Entrada_Banco"] - fluxo["Saida_Banco"]

    saldos_finais = mov.sort_values("Data").iloc[-1][["Saldo Caixa", "Saldo Banco", "Saldo Aplicações"]].to_frame(name="Saldo Final (R$)")

    html = (
        "<h2>Fluxo de Caixa</h2>" +
        fluxo.to_html(index=False, border=0) +
        "<h2>Saldos Consolidados</h2>" +
        saldos_finais.to_html(border=0)
    )
    return {"html": html}

def gerar_relatorio_administrativo():
    clientes = carregar_clientes()
    plantacoes = carregar_plantacoes()

    # 🛡️ Validações defensivas
    if clientes.empty:
        st.warning("⚠️ Nenhum cliente encontrado.")
        st.stop()
    if plantacoes.empty:
        st.warning("⚠️ Nenhuma plantação encontrada.")
        st.stop()
    if "cliente_id" not in clientes.columns or "Cliente" not in clientes.columns:
        st.error("❌ Colunas 'cliente_id' ou 'Cliente' ausentes no DataFrame de clientes.")
        st.stop()
    if "cliente_id" not in plantacoes.columns or "Estado" not in plantacoes.columns:
        st.error("❌ Colunas 'cliente_id' ou 'Estado' ausentes no DataFrame de plantações.")
        st.stop()

    # 🔄 Merge e relatórios
    merged = plantacoes.merge(clientes[["cliente_id", "Cliente"]], on="cliente_id", how="left",suffixes=('', '_cli'))
    
    cli_estado = (
        merged.groupby("Estado")["Cliente"]
        .nunique()
        .reset_index()
        .rename(columns={"Cliente": "Qtd Clientes"})
        .sort_values("Qtd Clientes", ascending=False)
    )

    top_culturas = (
        plantacoes["cultura"]
        .value_counts()
        .head(10)
        .reset_index()
        .rename(columns={"index": "Cultura", "cultura": "Nº Plantações"})
    )

    tipos_solo = (
        plantacoes["tipo_solo"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Tipo Solo", "tipo_solo": "Qtd"})
    )

    html = (
        "<h2>Clientes por Estado</h2>"
        + cli_estado.to_html(index=False, border=0)
        + "<h2>Top 10 Culturas</h2>"
        + top_culturas.to_html(index=False, border=0)
        + "<h2>Tipos de Solo</h2>"
        + tipos_solo.to_html(index=False, border=0)
    )

    return {
        "df_estados": cli_estado,
        "df_culturas": top_culturas,
        "df_solos": tipos_solo,
        "html": html,
    }


# ===============================
# 📤 ENVIO DE E-MAIL
# ===============================

def enviar_email(destinatarios, assunto, corpo_html):
    try:
        for destinatario in destinatarios:
            msg = EmailMessage()
            msg["Subject"] = assunto
            msg["From"] = email_remetente
            msg["To"] = destinatario
            msg.set_content("Seu e-mail não suporta HTML. Use um cliente compatível.")
            msg.add_alternative(corpo_html, subtype="html")

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(email_remetente, senha)
                smtp.send_message(msg)

        st.success("✅ E-mail enviado com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao enviar e-mail: {e}")

# ===============================
# 🎨 INTERFACE STREAMLIT
# ===============================

# 📧 Credenciais
email_remetente = "gsittonc@gmail.com"
senha = "zfwp rbmp wnig pcwb"  # Senha de app do Gmail
destinatarios = ["gsittonc@gmail.com"]

st.set_page_config(page_title="Enviar Relatórios por E-mail", page_icon="📧")
st.title("📤 Envio Automático de Relatórios")

st.markdown("### Selecione um relatório para enviar:")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📈 Vendas"):
        rel = gerar_relatorio_vendas()
        enviar_email(destinatarios, "📊 Relatório de Vendas", rel["html"])

with col2:
    if st.button("💰 Financeiro"):
        rel = gerar_relatorio_financeiro()
        enviar_email(destinatarios, "📊 Relatório Financeiro", rel["html"])

with col3:
    if st.button("📋 Administrativo"):
        rel = gerar_relatorio_administrativo()
        enviar_email(destinatarios, "📊 Relatório Administrativo", rel["html"])
