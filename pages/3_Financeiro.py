import streamlit as st
from supabase_utils import carregar_clientes, carregar_vendas, carregar_itens_venda, carregar_plantacoes, carregar_produtos, excluir_cliente, requer_autenticacao,restore_from_cookie

st.title("📊 Dashboards Financeiros")
st.write("Este é o dashboard financeiro do seu sistema.")
restore_from_cookie()
requer_autenticacao()
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from supabase_utils import supabase


# === CARREGAR DADOS ===
@st.cache_data
def carregar_movfinanceiro():
    res = supabase.table("movfinanceiro").select("*").execute()
    df = pd.DataFrame(res.data)
    df["Data"] = pd.to_datetime(df["Data"], format='ISO8601', utc=True)
    return df.sort_values("Data")

df = carregar_movfinanceiro()

# === FILTROS ===
st.sidebar.header("Filtros")
tipo_evento = st.sidebar.multiselect("Tipo Evento", options=df["Tipo Evento"].unique(), default=df["Tipo Evento"].unique())

import pytz

utc = pytz.UTC
data_inicio = utc.localize(pd.to_datetime(st.sidebar.date_input("Data inicial", df["Data"].min().date())))
data_fim = utc.localize(pd.to_datetime(st.sidebar.date_input("Data final", df["Data"].max().date())))
cols_numericas = ["Entrada Caixa", "Saída Caixa", "Entrada Banco", "Saída Banco",
                      "Saldo Caixa", "Saldo Banco", "Saldo Aplicações"]
df[cols_numericas] = df[cols_numericas].apply(pd.to_numeric, errors="coerce")
df[cols_numericas] = df[cols_numericas].fillna(0)
df_filtrado = df[
    (df["Data"] >= data_inicio) &
    (df["Data"] <= data_fim) &
    (df["Tipo Evento"].isin(tipo_evento))
]


# === KPIs ===
from datetime import datetime

# Buscar a linha com data mais próxima da data atual
data_hoje = pd.Timestamp(datetime.now().date(), tz="UTC")
df_mais_recente = df.loc[df["Data"] <= data_hoje].sort_values("Data").iloc[-1]
col1, col2, col3 = st.columns(3)
col1.metric("Saldo Caixa Atual", f"R$ {df_mais_recente['Saldo Caixa']:,.2f}")
col2.metric("Saldo Banco Atual", f"R$ {df_mais_recente['Saldo Banco']:,.2f}")
col3.metric("Saldo Aplicações Atual", f"R$ {df_mais_recente['Saldo Aplicações']:,.2f}")

# === GRÁFICOS ===
st.subheader("Evolução dos Saldos")
fig_saldos = px.line(
    df_filtrado,
    x="Data",
    y=["Saldo Caixa", "Saldo Banco", "Saldo Aplicações"],
    labels={"value": "R$", "variable": "Conta"},
    title="Saldos ao longo do tempo"
)
st.plotly_chart(fig_saldos, use_container_width=True)

st.subheader("Entradas e Saídas por Mês")
df_filtrado["AnoMes"] = df_filtrado["Data"].dt.to_period("M").astype(str)

df_agg = df_filtrado.groupby("AnoMes")[["Entrada Caixa", "Saída Caixa", "Entrada Banco", "Saída Banco"]].sum().reset_index()
fig_bar = px.bar(
    df_agg,
    x="AnoMes",
    y=["Entrada Caixa", "Saída Caixa", "Entrada Banco", "Saída Banco"],
    barmode="group",
    title="Fluxo de Caixa e Banco por Mês"
)
st.plotly_chart(fig_bar, use_container_width=True)


# === TABELA ===
st.subheader("Tabela de Eventos Financeiros")
st.dataframe(df_filtrado, use_container_width=True)
