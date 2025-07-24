import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

from supabase_utils import (
    carregar_vendas1,
    carregar_clientes1,
    carregar_itens_venda1,
    carregar_produtos1,
    carregar_plantacoes1,
    autenticar_usuario,
    desconectar_usuario,restore_from_cookie, persist_to_cookie, clear_cookies,CookieController,
    get_or_create_device_id,registrar_dispositivo_autorizado,dispositivo_autorizado

)

# -------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA & SESSÃO
# -------------------------------------------------------------
st.set_page_config(page_title="Rico Orgânicos - Dashboard", layout="wide")
st.title("🌱 Rico Orgânicos")

COOKIE_MAX_AGE = int(os.getenv("COOKIE_MAX_AGE", 86400))  # fallback para 24h
COOKIE_PREFIX = os.getenv("COOKIE_PREFIX", "rico_auth")
cookie = CookieController()

# --- Inicializa st.session_state (login) ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    restore_from_cookie()
# 🚨 Verifica se o device atual ainda é autorizado, mesmo que o cookie exista
if st.session_state.get("logado"):
    device_id = get_or_create_device_id()
    email = st.session_state.get("user_email")
    if not dispositivo_autorizado(email, device_id):
        clear_cookies()
        st.session_state.clear()
        st.warning("🚫 Este dispositivo não está mais autorizado. Faça login novamente.")
        st.stop()
# Expiração manual (garantia extra)
if st.session_state.get("logado"):
    if datetime.now() - st.session_state.login_time > timedelta(seconds=COOKIE_MAX_AGE):
        clear_cookies()
        st.session_state.clear()
        st.warning("⏰ Sessão expirada. Faça login novamente.")
        st.stop()

# -------------------------------------------------------------
# FORMULÁRIO DE LOGIN
# -------------------------------------------------------------
if not st.session_state.get("logado"):
    st.subheader("🔐 Login necessário")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    # Tentativa de login
    if st.button("Entrar") and email and senha:
        user = autenticar_usuario(email, senha)
        if user and user.user:
            device_id = get_or_create_device_id()

            if dispositivo_autorizado(email, device_id):
                # Dispositivo autorizado → login completo
                st.session_state.update({
                    "token": user.session.access_token,
                    "user_email": user.user.email,
                    "login_time": datetime.now(),
                    "logado": True,
                })
                persist_to_cookie()
                st.success(f"✅ Logado como {user.user.email}")
                st.rerun()
            else:
                # Salva dados para autorizar depois
                st.session_state.pending_auth = {
                    "email": email,
                    "device_id": device_id,
                    "session": user.session
                }
                st.warning("⚠️ Este dispositivo ainda não está autorizado.")
                st.rerun()
        else:
            st.error("❌ Falha no login. Verifique email e senha.")

    # Tela de autorização de dispositivo
    elif "pending_auth" in st.session_state:
        st.warning("⚠️ Este dispositivo ainda não está autorizado.")
        if st.button("Autorizar este dispositivo"):
            dados = st.session_state.pending_auth
            registrar_dispositivo_autorizado(dados["email"], dados["device_id"])
            del st.session_state["pending_auth"]
            st.success("✅ Dispositivo autorizado. Faça login novamente.")
            st.rerun()

    st.stop()


# -------------------------------------------------------------
# SIDEBAR – logout
# -------------------------------------------------------------
with st.sidebar:
    st.markdown(f"👤 **Usuário:** {st.session_state.user_email}")
    if st.button("Sair"):
        desconectar_usuario()
        clear_cookies()
        st.session_state.clear()
        st.rerun()


# ⚠️ Estas funções devem ser adaptadas para aceitar token, se ainda não forem.
token = st.session_state.get("token")

vendas_df = carregar_vendas1(token=token)
itens_df = carregar_itens_venda1(token=token)
produtos_df = carregar_produtos1(token=token)
plantacoes_df = carregar_plantacoes1(token=token)


# ========== DASHBOARD ==========
vendas_df["data_venda"] = pd.to_datetime(vendas_df["data_venda"], errors="coerce")

def converter_valor_brasileiro(valor_str):
    try:
        return float(valor_str.replace(".", "").replace(",", "."))
    except:
        return None

vendas_df["valor_venda"] = vendas_df["valor_venda"].apply(converter_valor_brasileiro)

hoje = pd.Timestamp.today()
doze_meses_atras = hoje - pd.DateOffset(months=12)

faturamento_total = vendas_df["valor_venda"].sum()
faturamento_12m = vendas_df[vendas_df["data_venda"] >= doze_meses_atras]["valor_venda"].sum()
regioes_ativas = plantacoes_df["Estado"].dropna().nunique()

itens_df["faturamento"] = itens_df["quantidade"] * itens_df["valor_unitario"]
qtd_por_produto = itens_df.groupby("produto_id")["quantidade"].sum().reset_index()
faturamento_produto = itens_df.groupby("produto_id")["faturamento"].sum().reset_index()

qtd_por_produto = qtd_por_produto.merge(produtos_df, on="produto_id", how="left")
faturamento_produto = faturamento_produto.merge(produtos_df, on="produto_id", how="left")

qtd_por_produto = qtd_por_produto.sort_values(by="quantidade", ascending=False)
faturamento_produto = faturamento_produto.sort_values(by="faturamento", ascending=False)

# === KPIs ===
col1, col2, col3 = st.columns(3)
col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("📅 Últimos 12 meses", f"R$ {faturamento_12m:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("📍 Regiões Ativas", regioes_ativas)

# === Gráfico por Estado ===
st.markdown("## 📊 Faturamento por Estado")
vendas_plantacoes = vendas_df.merge(plantacoes_df[["cliente_id", "Estado"]], on="cliente_id", how="left")
vendas_plantacoes["Estado"] = vendas_plantacoes["Estado"].str.strip()
vendas_plantacoes = vendas_plantacoes.dropna(subset=["Estado"])
faturamento_estado = vendas_plantacoes.groupby("Estado")["valor_venda"].sum().reset_index()

fig = px.pie(
    faturamento_estado,
    names="Estado",
    values="valor_venda",
    title="Faturamento Total por Estado",
    color_discrete_sequence=px.colors.sequential.Viridis_r,
)
fig.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig, use_container_width=True)

# === Tabelas ===
faturamento_produto["faturamento"] = faturamento_produto["faturamento"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 🧮 Quantidade por Produto")
    st.dataframe(qtd_por_produto[["Produto", "quantidade"]].rename(columns={"quantidade": "Quantidade"}))
with col2:
    st.markdown("#### 💵 Faturamento por Produto")
    st.dataframe(faturamento_produto[["Produto", "faturamento"]].rename(columns={"faturamento": "Faturamento (R$)"}))
