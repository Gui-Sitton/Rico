import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from streamlit_cookies_controller import CookieController
import os
from dotenv import load_dotenv
from supabase import create_client, Client
# === CONFIGURAÇÕES ===
st.set_page_config(page_title="Rico Orgânicos", layout="wide")

# Carrega variáveis de ambiente do .env
load_dotenv()

# Busca variáveis
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Valida se estão presentes
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL ou SUPABASE_KEY não foram definidas no .env")

# Cria o cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
#############################################################################
def inserir_venda_autenticada(dados, token):
    try:
        response = supabase.table("vendas").insert({
            "cliente_id": dados["cliente_id"],
            "data_venda": dados["data_venda"],
            "valor_venda": dados["valor_venda"]
        }).execute()
        return True
    except Exception as e:
        print(f"Erro ao inserir venda: {e}")
        return False

# === FUNÇÕES DE BANCO DE DADOS ===
def excluir_vendas_por_cliente(cliente_id):
    try:
        response = supabase.table("vendas").delete().eq("cliente_id", cliente_id).execute()
        return True
    except Exception as e:
        print(f"Erro ao excluir vendas do cliente {cliente_id}: {e}")
        return False

def carregar_clientes():
    try:
        response = supabase.table("clientes").select("*").order("cliente_id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {e}")
        return pd.DataFrame()
def carregar_movfinanceiro():
    try:
        response = supabase.table("movfinanceiro").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar movimentações financeiras: {e}")
        return pd.DataFrame()
def carregar_vendas():
    try:
        response = supabase.table("vendas").select("*").order("venda_id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar vendas: {e}")
        return pd.DataFrame()

def carregar_produtos():
    try:
        response = supabase.table("produtos").select("*").order("produto_id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar produtos: {e}")
        return pd.DataFrame()

def carregar_plantacoes():
    try:
        response = supabase.table("plantacoes").select("*").order("plantacao_id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar plantacoes: {e}")
        return pd.DataFrame()

def carregar_itens_venda():
    try:
        response = supabase.table("itens_venda").select("*").order("item_venda_id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar itens_venda: {e}")
        return pd.DataFrame()

# === AUTENTICAÇÃO ===
def autenticar_usuario(email: str, senha: str):
    try:
        return supabase.auth.sign_in_with_password({"email": email, "password": senha})
    except Exception as e:
        st.error(f"Erro ao autenticar: {e}")
        return None
# em utils.py
def requer_autenticacao():
    import streamlit as st
    from datetime import datetime, timedelta
    import os
    from streamlit_cookies_controller import CookieController
    from supabase_utils import restore_from_cookie, clear_cookies  # ajuste conforme seu módulo

    # Parâmetros de expiração
    COOKIE_MAX_AGE = int(os.getenv("COOKIE_MAX_AGE", 86400))  # padrão: 24h

    # Tenta restaurar a sessão, se necessário
    if "logado" not in st.session_state or not st.session_state.get("logado"):
        restore_from_cookie()

    # Verifica se está logado após restaurar
    if st.session_state.get("logado"):
        login_time = st.session_state.get("login_time", datetime.min)
        if datetime.now() - login_time > timedelta(seconds=COOKIE_MAX_AGE):
            clear_cookies()
            st.session_state.clear()
            st.warning("⏰ Sessão expirada. Faça login novamente.")
            st.stop()
    else:
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        st.stop()


def obter_token_usuario():
    import streamlit as st
    return st.session_state.get("token")

def desconectar_usuario():
    try:
        supabase.auth.sign_out()
    except Exception as e:
        st.error(f"Erro ao desconectar: {e}")

# === INSERÇÃO AUTENTICADA ===
  # ← cliente já autenticado
def inserir_item_venda_autenticado(dados, token):
    try:
        response = supabase.table("itens_venda").insert({
            "venda_id": dados["venda_id"],
            "produto_id": dados["produto_id"],
            "quantidade": dados["quantidade"],
            "valor_unitario": dados["valor_unitario"],
        }).execute()

        if response.data:
            return True
        else:
            st.error("❌ Inserção não retornou dados. Verifique os campos ou restrições da tabela.")
            return False

    except Exception as e:
        st.error(f"❌ Erro ao inserir item da venda: {e}")
        return False
def inserir_plantacao_autenticada(dados, token):
    try:
        response = supabase.table("plantacoes").insert({
            "cliente_id": dados["cliente_id"],
            "Cliente": dados["Cliente"],
            "cultura": dados["cultura"],
            "tipo_solo": dados["tipo_solo"],
            "Cidade": dados["Cidade"],
            "Estado": dados["Estado"],
            "latitude": dados["latitude"],
            "longitude": dados["longitude"]
        }).execute()

        if response.data:
            return True
        else:
            st.error("❌ Inserção não retornou dados. Verifique os campos ou restrições da tabela.")
            return False

    except Exception as e:
        st.error(f"❌ Erro ao inserir plantação: {e}")
        return False


def inserir_cliente_autenticado(dados, token):
    try:
        response = supabase.table("clientes").insert({
            "Cliente": dados["Cliente"],
            "cpf_cnpj": dados["cpf_cnpj"],
            "telefone": dados["telefone"],
            "email": dados["email"],
            "data_cadastro": dados["data_cadastro"]
        }).execute()

        if response.data:
            return True
        else:
            st.error("❌ Inserção não retornou dados. Verifique se o cliente já existe ou se há erros de validação.")
            return False

    except Exception as e:
        st.error(f"❌ Erro ao inserir cliente autenticado: {e}")
        return False
def excluir_cliente(cliente_id):
    try:
        response = supabase.table("clientes").delete().eq("cliente_id", cliente_id).execute()

        if response.data:
            st.success(f"✅ Cliente ID {cliente_id} removido com sucesso.")
            return True
        else:
            st.warning("⚠️ Nenhum cliente foi excluído. Verifique o ID.")
            return False

    except Exception as e:
        st.error(f"❌ Erro ao excluir cliente: {e}")
        return False


def requer_autenticacao():
    if "token" not in st.session_state or st.session_state["token"] is None:
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        st.stop()


def excluir_itens_venda_por_cliente(cliente_id):
    try:
        # Primeiro busca todas as vendas do cliente
        vendas = supabase.table("vendas").select("venda_id").eq("cliente_id", cliente_id).execute()
        if vendas.data:
            for venda in vendas.data:
                supabase.table("itens_venda").delete().eq("venda_id", venda["venda_id"]).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao excluir itens de venda: {e}")
        return False

def excluir_vendas_por_cliente(cliente_id):
    try:
        supabase.table("vendas").delete().eq("cliente_id", cliente_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao excluir vendas: {e}")
        return False

def excluir_plantacoes_por_cliente(cliente_id):
    try:
        supabase.table("plantacoes").delete().eq("cliente_id", cliente_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao excluir plantações: {e}")
        return False

def excluir_cliente(cliente_id):
    try:
        supabase.table("clientes").delete().eq("cliente_id", cliente_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao excluir cliente: {e}")
        return False


def inserir_movfinanceiro(dados: dict):
    try:
        response = supabase.table("movfinanceiro").insert(dados).execute()

        if response.status_code == 201:
            return True
        else:
            print("Erro ao inserir:", response)
            return False
    except Exception as e:
        print("Erro na inserção no Supabase:", e)
        return False

import math

def safe_value(val):
    if val is None:
        return 0
    try:
        if math.isnan(val):
            return 0
    except:
        pass
    return val

# Função auxiliar para gerar o valor mais relevante (entrada ou saída)
def extrair_valor_evento(row):
    for col in [
        "Entrada Caixa", "Saída Caixa", "Entrada Banco", 
        "Saída Banco", "Aplicações"
    ]:
        if pd.notna(row[col]) and row[col] != 0:
            return f"R$ {row[col]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ 0,00"

# Função para atualizar saldo no Supabase (implemente aqui a chamada real do seu client)
def atualizar_saldo_no_supabase(evento_id, coluna_saldo, valor):
    try:
        res = supabase.table("movfinanceiro").update({coluna_saldo: valor}).eq("evento_id", evento_id).execute()
        
        if not res.data:
            st.error("❌ Supabase não retornou dados. Verifique o evento_id.")
    except Exception as e:
        st.error(f"❌ Exceção ao atualizar saldo no Supabase: {e}")


# Função para recalcular saldos de uma categoria a partir de data_inicio
def recalcular_saldos_categoria(df, categoria, data_inicio):
    # Garante que a coluna Data seja datetime real (com hora)
    df["Data"] = pd.to_datetime(df["Data"],utc=True, errors="coerce")

    # Filtra eventos com Data >= data_inicio (agora com hora, não apenas .date())
    df_cat = df[df["Data"] >= data_inicio].copy()

    # Ordena corretamente só por Data (com fallback pelo evento_id)
    df_cat = df_cat.sort_values(by=["Data", "evento_id"], ascending=[True, True])

    # Busca o último saldo conhecido antes da data de início
    df_antes = df[df["Data"] < data_inicio]
    if not df_antes.empty:
        ultimo_antes = df_antes.sort_values(by=["Data", "evento_id"], ascending=[True, True]).iloc[-1]
        saldo_acumulado = safe_value(ultimo_antes.get(f"Saldo {categoria}"))
    else:
        saldo_acumulado = 0

    # Percorre os eventos e recalcula os saldos
    for idx, row in df_cat.iterrows():
        if row["evento_id"] is None:
            continue  # ignora linhas sem ID

        entrada = safe_value(row.get(f"Entrada {categoria}"))
        saida = safe_value(row.get(f"Saída {categoria}"))
        saldo_acumulado += entrada - saida

        df_cat.at[idx, f"Saldo {categoria}"] = saldo_acumulado

        #st.write(f"🔁 Recalculando saldo para evento {row['evento_id']} ({row['Data']})")

        # Só tenta atualizar se for um evento_id realmente existente
        if int(row["evento_id"]) > 200:  # ou use outro filtro mais inteligente
            atualizar_saldo_no_supabase(row["evento_id"], f"Saldo {categoria}", saldo_acumulado)
def recalcular_saldos_totais(df):
    """
    Recalcula saldo de Caixa, Banco e Aplicações para o
    DataFrame inteiro, em ordem de Data ↑, evento_id ↑,
    e sincroniza o Supabase quando algo mudar.
    """
    # Garantir datetime válido
    df = df.copy()
    df["Data"] = pd.to_datetime(df["Data"], utc=True, errors="coerce")
    df = df.sort_values(["Data", "evento_id"], ascending=[True, True])

    saldo_caixa = saldo_banco = saldo_aplic = 0.0

    for idx, row in df.iterrows():
        entrada_caixa = safe_value(row.get("Entrada Caixa"))
        saida_caixa   = safe_value(row.get("Saída Caixa"))
        entrada_banco = safe_value(row.get("Entrada Banco"))
        saida_banco   = safe_value(row.get("Saída Banco"))
        aplicacoes    = safe_value(row.get("Aplicações"))

        saldo_caixa += entrada_caixa - saida_caixa
        saldo_banco += entrada_banco - saida_banco
        saldo_aplic += aplicacoes              # só positivo

        # Atualiza no DataFrame (útil para debug local / Streamlit)
        df.at[idx, "Saldo Caixa"]       = saldo_caixa
        df.at[idx, "Saldo Banco"]       = saldo_banco
        df.at[idx, "Saldo Aplicações"]  = saldo_aplic

        # Sincroniza Supabase se algum valor mudou
        if (row["Saldo Caixa"]       != saldo_caixa or
            row["Saldo Banco"]       != saldo_banco or
            row["Saldo Aplicações"]  != saldo_aplic):

            supabase.table("movfinanceiro").update(
                {
                    "Saldo Caixa":      saldo_caixa,
                    "Saldo Banco":      saldo_banco,
                    "Saldo Aplicações": saldo_aplic
                }
            ).eq("evento_id", row["evento_id"]).execute()

            #st.write(f"🔄 evento {row['evento_id']} — saldos ajustados")

def excluir_evento_por_id(evento_id):
    try:
        res = supabase.table("movfinanceiro").delete().eq("evento_id", evento_id).execute()

        if res.data:  # Se veio algum dado, significa que o evento foi deletado
            st.success(f"✅ Evento {evento_id} excluído com sucesso.")
            return True
        else:
            st.warning(f"⚠️ Nenhum evento com ID {evento_id} encontrado ou já foi excluído.")
            st.write("📦 Resposta Supabase:", res)
            return False

    except Exception as e:
        st.error(f"❌ Exceção ao excluir evento: {e}")
        return False



COOKIE_MAX_AGE = 24 * 60 * 60          # 24h em segundos
COOKIE_PREFIX  = "rico_auth"           # evita colisão com outros apps

cookie = CookieController()            # componente

def restore_from_cookie():
    token     = cookie.get(f"{COOKIE_PREFIX}_token")
    email     = cookie.get(f"{COOKIE_PREFIX}_email")
    ts        = cookie.get(f"{COOKIE_PREFIX}_ts")
    device_id = cookie.get(f"{COOKIE_PREFIX}_device")

    print(f"[DEBUG] restore_from_cookie: token={token}, email={email}, ts={ts}, device_id={device_id}")

    # Verificações básicas
    if not all([token, email, ts, device_id]):
        print("[DEBUG] restore_from_cookie: dados incompletos, não restaura sessão")
        return

    if time.time() - float(ts) > COOKIE_MAX_AGE:
        print("[DEBUG] restore_from_cookie: cookie expirado")
        clear_cookies()
        return

    # Verifica se o dispositivo está autorizado no Supabase
    if not dispositivo_autorizado(email, device_id):
        print("[DEBUG] restore_from_cookie: dispositivo NÃO autorizado")
        clear_cookies()
        return

    # Restaura a sessão
    st.session_state.update({
        "token": token,
        "user_email": email,
        "login_time": datetime.now(),
        "logado": True
    })
    print("[DEBUG] restore_from_cookie: sessão restaurada com sucesso")


    # Checa no banco se dispositivo está autorizado
    if dispositivo_autorizado(email, device_id):
        st.session_state.update({
            "logado": True,
            "token": token,
            "user_email": email,
            "login_time": datetime.fromtimestamp(float(ts)),
        })
        print("[DEBUG] restore_from_cookie: sessão restaurada com sucesso")
    else:
        print("[DEBUG] restore_from_cookie: dispositivo não autorizado - limpando sessão")
        clear_cookies()
        st.session_state.clear()
        st.warning("🚫 Dispositivo não autorizado. Faça login.")
        st.stop()

def persist_to_cookie():
    """Grava cookies associados ao dispositivo atual."""
    token = st.session_state.get("token")
    email = st.session_state.get("user_email")
    device_id = get_or_create_device_id()
    now = str(int(time.time()))

    for k, v in {
        f"{COOKIE_PREFIX}_token": token,
        f"{COOKIE_PREFIX}_email": email,
        f"{COOKIE_PREFIX}_device": device_id,
        f"{COOKIE_PREFIX}_ts": now,
    }.items():
        cookie.set(k, v, max_age=COOKIE_MAX_AGE,
                   secure=True, same_site="Strict")
  # boas práticas

def clear_cookies():
    for suffix in ("token", "email", "ts"):
        cookie.remove(f"{COOKIE_PREFIX}_{suffix}")



################################

import requests

def carregar_tabela(tabela, token=None, order_by=None, desc=True):
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tabela}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {token if token else SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        params = {
            "select": "*"
        }
        if order_by:
            ordem = "desc" if desc else "asc"
            params["order"] = f"{order_by}.{ordem}"

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            st.error(f"Erro ao carregar {tabela}: {response.text}")
            return pd.DataFrame()
        
        return pd.DataFrame(response.json())
    
    except Exception as e:
        st.error(f"Erro inesperado ao carregar {tabela}: {e}")
        return pd.DataFrame()

# Funções específicas usando a genérica:
def carregar_vendas1(token=None):
    return carregar_tabela("vendas", token=token, order_by="venda_id")

def carregar_itens_venda1(token=None):
    return carregar_tabela("itens_venda", token=token, order_by="item_venda_id")

def carregar_produtos1(token=None):
    return carregar_tabela("produtos", token=token, order_by="produto_id")

def carregar_plantacoes1(token=None):
    return carregar_tabela("plantacoes", token=token, order_by="plantacao_id")

def carregar_clientes1(token=None):
    return carregar_tabela("clientes", token=token, order_by="cliente_id")
def carregar_movfinanceiro1(token=None):
    return carregar_tabela("movfinanceiro", token=token, order_by="evento_id")



import uuid

def get_or_create_device_id():
    device_id = cookie.get(f"{COOKIE_PREFIX}_device_id")
    if not device_id:
        device_id = str(uuid.uuid4())  # único por navegador
        cookie.set(f"{COOKIE_PREFIX}_device_id", device_id, max_age=COOKIE_MAX_AGE, secure=True, same_site="strict")
    return device_id



def registrar_dispositivo_autorizado(email, device_id):
    """Registra o device_id como autorizado para esse usuário."""
    supabase.table("dispositivos_autorizados").insert({
        "email": email,
        "device_id": device_id,
        "registrado_em": datetime.now().isoformat()
    }).execute()


def dispositivo_autorizado(email, device_id):
    result = supabase.table("dispositivos_autorizados")\
        .select("*")\
        .eq("email", email)\
        .eq("device_id", device_id)\
        .execute()
    return len(result.data) > 0
