import streamlit as st
from streamlit_calendar import calendar
from supabase_utils import carregar_movfinanceiro1, inserir_movfinanceiro,safe_value,extrair_valor_evento,atualizar_saldo_no_supabase,recalcular_saldos_categoria,recalcular_saldos_totais,excluir_evento_por_id
import pandas as pd
import math
from datetime import datetime
import time
from datetime import timezone
from supabase_utils import supabase, restore_from_cookie, persist_to_cookie, clear_cookies,CookieController  # ✅ isso importa o client corretamente
import os
st.title("📅 Calendário Financeiro")
token = st.session_state.get("token")
#######
COOKIE_MAX_AGE = int(os.getenv("COOKIE_MAX_AGE", 86400))  # fallback para 24h
COOKIE_PREFIX = os.getenv("COOKIE_PREFIX", "rico_auth")
cookie = CookieController()
restore_from_cookie()
# --- Inicializa st.session_state (login) ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    restore_from_cookie()

########

df = carregar_movfinanceiro1(token=token)
df["Data"] = pd.to_datetime(df["Data"], dayfirst=False, errors="coerce")
df = df[df["Tipo Evento"] != "Saldo mantido"]
if "Data" not in df.columns:
    st.error("❌ Coluna 'Data' não encontrada.")
    st.stop()

# Função auxiliar para gerar o valor mais relevante (entrada ou saída)
def extrair_valor_evento(row):
    for col in [
        "Entrada Caixa", "Saída Caixa", "Entrada Banco", 
        "Saída Banco", "Aplicações"
    ]:
        if pd.notna(row[col]) and row[col] != 0:
            return f"R$ {row[col]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ 0,00"

# Criação dos eventos para o calendário
events = []
for _, row in df.iterrows():
    if pd.notna(row["Data"]) and row["Tipo Evento"] != "Saldo mantido":

        # Determinar a cor do evento com base no tipo
        tipo = row["Tipo Evento"]
        if "Entrada" in tipo:
            cor = "#28a745"  # verde
        elif "Saída" in tipo:
            cor = "#dc3545"  # vermelho
        else:
            cor = "#0d6efd"  # azul padrão (opcional para outros tipos)

        evento = {
            "title": row.get("Histórico", "Sem observação"),
            "start": row["Data"].strftime("%Y-%m-%d"),
            "allDay": True,
            "color": cor,
            "extendedProps": {
                "Histórico": row.get("Histórico", "Sem observação"),
                "Tipo Evento": row.get("Tipo Evento", "Não informado"),
                "Valor": extrair_valor_evento(row),
                "Entrada Caixa": safe_value(row.get("Entrada Caixa")),
                "Entrada Banco": safe_value(row.get("Entrada Banco")),
                "Saída Caixa": safe_value(row.get("Saída Caixa")),
                "Saída Banco": safe_value(row.get("Saída Banco")),
                "Saldo Caixa": safe_value(row.get("Saldo Caixa")),
                "Saldo Banco": safe_value(row.get("Saldo Banco")),
                "Saldo Aplicações": safe_value(row.get("Saldo Aplicações")),
                }

        }
        events.append(evento)



# Configuração visual do calendário
options = {
    "initialView": "dayGridMonth",
    "locale": "pt-br",
    "height": 700,
    "eventClick": True,  # Para permitir clicar nos eventos
}
from datetime import datetime, timedelta

hoje = datetime.now().date()

# Criar coluna só com a data (sem horário)
df["Data_Somente_Data"] = df["Data"].dt.date

# Filtra registros do dia atual
df_hoje = df[df["Data_Somente_Data"] == hoje]
##############
# Filtrar registros com pelo menos 1 saldo não nulo
df_validos = df.dropna(subset=["Saldo Caixa", "Saldo Banco", "Saldo Aplicações"], how="all")

if not df_validos.empty:
    # Tenta pegar o dia de hoje primeiro
    df_hoje = df_validos[df_validos["Data_Somente_Data"] == hoje]
    if not df_hoje.empty:
        saldo_registro = df_hoje.sort_values("Data", ascending=False).iloc[0]
    else:
        # Pega o último dia anterior com saldo válido
        datas_anteriores = df_validos[df_validos["Data_Somente_Data"] < hoje]["Data_Somente_Data"].unique()
        if len(datas_anteriores) == 0:
            st.warning("Não há registros anteriores com saldos válidos.")
            saldo_registro = None
        else:
            dia_mais_recente = max(datas_anteriores)
            df_dia_recente = df_validos[df_validos["Data_Somente_Data"] == dia_mais_recente]
            saldo_registro = df_dia_recente.sort_index(ascending=False).iloc[0]
else:
    st.warning("Nenhum registro válido com saldos encontrado.")
    saldo_registro = None
        
######################
if saldo_registro is not None:
    col1, col2, col3 = st.columns(3)

    def formatar_valor(v):
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    with col1:
        st.metric("Saldo Caixa", formatar_valor(saldo_registro['Saldo Caixa']))
    with col2:
        st.metric("Saldo Banco", formatar_valor(saldo_registro['Saldo Banco']))
    with col3:
        st.metric("Saldo Aplicações", formatar_valor(saldo_registro['Saldo Aplicações']))


# Renderização do calendário
# Renderização do calendário (somente visual)
calendar(events=events, options=options, key="calendar_financeiro")

# Lista de eventos para seleção manual
#nomes_eventos = [f"{e['start']} - {e['title']}" for e in events]
#evento_escolhido = st.selectbox("📌 Selecione um evento para ver detalhes:", nomes_eventos)

from datetime import datetime

def evento_mais_proximo(events):
    hoje = datetime.today().date()

    def distancia_do_hoje(e):
        data_evento = datetime.strptime(e["start"], "%Y-%m-%d").date()
        return abs((data_evento - hoje).days)

    return sorted(events, key=distancia_do_hoje)[0]
eventos_formatados = [f"{e['start']} - {e['title']}" for e in events]

evento_mais_prox = evento_mais_proximo(events)
evento_default = f"{evento_mais_prox['start']} - {evento_mais_prox['title']}"

evento_escolhido = st.selectbox("📅 Selecione um evento", eventos_formatados, index=eventos_formatados.index(evento_default))


# Busca o evento selecionado

evento_detalhado = next(e for e in events if f"{e['start']} - {e['title']}" == evento_escolhido)
props = evento_detalhado["extendedProps"]
def formatar_valor(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.subheader("📌 Detalhes do Evento Selecionado")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**Data:** {evento_detalhado['start']}")
    st.markdown(f"**Histórico:** {props.get('Histórico')}")
    st.markdown(f"**Tipo de Evento:** {props.get('Tipo Evento')}")
    st.markdown(f"**Valor:** {props.get('Valor')}")

with col2:
    campos_valores = {
        "Entrada Caixa": props.get('Entrada Caixa', 0),
        "Entrada Banco": props.get('Entrada Banco', 0),
        "Saída Caixa": props.get('Saída Caixa', 0),
        "Saída Banco": props.get('Saída Banco', 0),
        "Saldo Caixa": props.get('Saldo Caixa', 0),
        "Saldo Banco": props.get('Saldo Banco', 0),
        "Saldo Aplicações": props.get('Saldo Aplicações', 0),
    }

    for nome, valor in campos_valores.items():
        if valor != 0:
            st.markdown(f"**{nome}:** {formatar_valor(valor)}")


import pytz

# Inserção de evento manual
st.markdown("## ➕ Adicionar novo evento")

with st.form("novo_evento"):
    data_evento = st.date_input("Data do evento", value=datetime.today())
    historico = st.text_input("Histórico do evento")
    tipo = st.selectbox("Tipo de Evento", ["Entrada", "Saída"])
    conta = st.selectbox("Conta", ["Caixa", "Banco", "Aplicações"])
    valor = st.number_input("Valor", min_value=0.0, format="%.2f")
    submit = st.form_submit_button("Salvar")

    if submit:
        if "evento_id" not in df.columns:
            st.error("❌ Coluna 'evento_id' não encontrada na base.")
            st.stop()

        tz_sp = pytz.timezone("America/Sao_Paulo")
        data_evento_dt = tz_sp.localize(
            datetime.combine(data_evento, datetime.min.time())
        ).astimezone(pytz.utc)

        df_anteriores = df[df["Data"] <= data_evento_dt]
        df_anteriores = df_anteriores.sort_values(by=["Data", "evento_id"], ascending=[False, False])

        if not df_anteriores.empty:
            ultimo = df_anteriores.iloc[0]
            saldo_caixa_anterior = safe_value(ultimo.get("Saldo Caixa"))
            saldo_banco_anterior = safe_value(ultimo.get("Saldo Banco"))
            saldo_aplic_anterior = safe_value(ultimo.get("Saldo Aplicações"))
        else:
            saldo_caixa_anterior = saldo_banco_anterior = saldo_aplic_anterior = 0

        entrada = valor if tipo == "Entrada" else 0
        saida = valor if tipo == "Saída" else 0

        novo_saldo_caixa = saldo_caixa_anterior
        novo_saldo_banco = saldo_banco_anterior
        novo_saldo_aplic = saldo_aplic_anterior

        if conta == "Caixa":
            novo_saldo_caixa += entrada - saida
        elif conta == "Banco":
            novo_saldo_banco += entrada - saida
        elif conta == "Aplicações":
            novo_saldo_aplic += entrada

        novo = {
            "Data": data_evento_dt.isoformat(),
            "Histórico": historico,
            "Tipo Evento": tipo,
            "Entrada Caixa": valor if tipo == "Entrada" and conta == "Caixa" else 0,
            "Entrada Banco": valor if tipo == "Entrada" and conta == "Banco" else 0,
            "Saída Caixa": valor if tipo == "Saída" and conta == "Caixa" else 0,
            "Saída Banco": valor if tipo == "Saída" and conta == "Banco" else 0,
            "Aplicações": valor if conta == "Aplicações" else 0,
            "Saldo Caixa": novo_saldo_caixa,
            "Saldo Banco": novo_saldo_banco,
            "Saldo Aplicações": novo_saldo_aplic
        }

        inserir_movfinanceiro(novo)
        # Aguarda o novo evento aparecer no banco (no máximo 5 tentativas)
        tentativas = 0
        evento_achado = False
        while tentativas < 5:
            df = carregar_movfinanceiro1(token=token)
            if historico in df["Histórico"].values:
                evento_achado = True
                break
            time.sleep(2)
            tentativas += 1

        if not evento_achado:
            st.warning("⚠️ Salvando novo evento") # dá tempo de gravar no Supabase


        df = carregar_movfinanceiro1(token=token)

        # ───────────────────────── recálculo global ───────────────────────── #
        recalcular_saldos_totais(df)

# Mostra saldos finais só para conferência
        st.success(
            f"Reprocessado! Saldo Caixa: R$ {df['Saldo Caixa'].iloc[-1]:,.2f}  |  "
            f"Banco: R$ {df['Saldo Banco'].iloc[-1]:,.2f}  |  "
            f"Aplicações: R$ {df['Saldo Aplicações'].iloc[-1]:,.2f}"
        )
        st.write("Por favor, recarregue a página para ver o novo evento no calendário.")



st.markdown("## 🗑️ Excluir evento")

with st.expander("Excluir evento manualmente"):
    eventos_exibicao = df.sort_values("Data", ascending=True)
    opcoes = [
        f"{int(row.evento_id)} | {row['Data'].strftime('%Y-%m-%d')} | {row['Histórico']}"
        for _, row in eventos_exibicao.iterrows()
    ]
    evento_escolhido = st.selectbox("Selecione o evento a excluir:", opcoes)

    if st.button("Excluir evento selecionado"):
        evento_id_excluir = int(evento_escolhido.split(" | ")[0])
        data_referencia = df[df["evento_id"] == evento_id_excluir]["Data"].iloc[0]

        if excluir_evento_por_id(evento_id_excluir):
            # Recarrega a base após exclusão
            df = carregar_movfinanceiro1(token=token)

            # Recalcula saldos a partir da data do evento excluído
            recalcular_saldos_totais(df)
        st.write("Por favor, recarregue a página para ver as alterações no calendário.")


        

