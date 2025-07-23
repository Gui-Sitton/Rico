import streamlit as st
from supabase_utils import (
    inserir_cliente_autenticado,
    obter_token_usuario,
    requer_autenticacao,
    carregar_clientes1,
    inserir_venda_autenticada,
    carregar_plantacoes1,
    carregar_produtos1,
    inserir_item_venda_autenticado,
    inserir_plantacao_autenticada,
    carregar_vendas1,
    carregar_itens_venda1,restore_from_cookie  # Supondo que essa função retorna todos os clientes
)

st.set_page_config(page_title="Cadastro de Dados", layout="wide")
st.title("📥 Cadastro de Novos Dados")
restore_from_cookie()
requer_autenticacao()

token = st.session_state.get("token")

# === Input de cliente ===
st.header("🧍 Cadastrar Cliente")
nome = st.text_input("Nome/Razão Social")
cpf = st.text_input("CPF/CNPJ")
telefone = st.text_input("Telefone")
email = st.text_input("E-mail")
data = st.date_input("Data de Cadastro")

if st.button("Salvar Cliente"):
    if nome:
        token = st.session_state.get("token")
        if token:
            sucesso = inserir_cliente_autenticado({
                "Cliente": nome,
                "cpf_cnpj": cpf,
                "telefone": telefone,
                "email": email,
                "data_cadastro": str(data)
            }, token)
            if sucesso:
                st.success(f"✅ Cliente cadastrado com sucesso!")
            else:
                st.error("❌ Erro ao inserir cliente.")
        else:
            st.error("❌ Usuário não autenticado. Faça login antes de cadastrar.")
    else:
        st.warning("⚠️ Preencha ao menos o nome.")


st.divider()
st.header("🧾 Registrar Venda")

clientes = carregar_clientes1(token=token)

if not clientes.empty:
    opcoes_clientes = {
        f"{row['Cliente']} (ID: {row['cliente_id']})": row['cliente_id']
        for _, row in clientes.iterrows()
    }
    cliente_nome = st.selectbox("Selecionar Cliente", list(opcoes_clientes.keys()))
    cliente_id = opcoes_clientes[cliente_nome]

    data_venda = st.date_input("Data da Venda")
    valor_venda = st.number_input("Valor da Venda (R$)", min_value=0.0, format="%.2f")

    if st.button("Salvar Venda"):
        token = st.session_state.get("token")
        if token and cliente_id:
            sucesso = inserir_venda_autenticada({
                "cliente_id": cliente_id,
                "data_venda": str(data_venda),
                "valor_venda": valor_venda
            }, token)
            if sucesso:
                st.success("✅ Venda registrada com sucesso!")
            else:
                st.error("❌ Erro ao registrar a venda.")
        else:
            st.warning("⚠️ Usuário não autenticado ou cliente inválido.")
else:
    st.info("ℹ️ Nenhum cliente cadastrado ainda. Cadastre um cliente antes de registrar uma venda.")




# =============================
# === Input de Itens Venda ===
# =============================
st.divider()
st.header("📦 Cadastrar Itens da Venda")

vendas = carregar_vendas1(token=token)
produtos = carregar_produtos1(token=token)


if not vendas.empty and not produtos.empty:
    opcoes_vendas = {
        f"Venda {row['venda_id']} - Cliente ID {row['cliente_id']}": row['venda_id']
        for _, row in vendas.iterrows()
    }
    opcoes_produtos = {
        f"{row['Produto']} (ID: {row['produto_id']})": row['produto_id']
        for _, row in produtos.iterrows()
    }

    venda_nome = st.selectbox("Selecionar Venda", list(opcoes_vendas.keys()))
    produto_nome = st.selectbox("Selecionar Produto", list(opcoes_produtos.keys()))

    venda_id = opcoes_vendas[venda_nome]
    produto_id = opcoes_produtos[produto_nome]

    quantidade = st.number_input("Quantidade (kg ou L)", min_value=0.0, format="%.2f")
    valor_unitario = st.number_input("Preço Unitário (R$)", min_value=0.0, format="%.2f")
    quantidade_int = int(quantidade)
    if st.button("Salvar Item de Venda"):
        token = st.session_state.get("token")
        if token and venda_id and produto_id:
            sucesso = inserir_item_venda_autenticado({
                "venda_id": venda_id,
                "produto_id": produto_id,
                "quantidade": quantidade_int,
                "valor_unitario": valor_unitario
            }, token)
            if sucesso:
                st.success("✅ Item de venda cadastrado com sucesso!")
            else:
                st.error("❌ Erro ao registrar o item da venda.")
        else:
            st.warning("⚠️ Usuário não autenticado ou dados inválidos.")
else:
    st.info("ℹ️ Certifique-se de que há vendas e produtos cadastrados antes.")


# =============================
# === Input de Plantação ===
# =============================
st.divider()
st.header("🌾 Cadastrar Plantação")

if not clientes.empty:
    cliente_nome_plantacao = st.selectbox("Selecionar Cliente para Plantação", list(opcoes_clientes.keys()))
    cliente_id_plantacao = opcoes_clientes[cliente_nome_plantacao]

    cultura = st.text_input("Cultura (ex: Soja, Milho, Café)")
    tipo_solo = st.text_input("Tipo de Solo (ex: Arenoso, Argiloso)")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado (UF)")
    latitude = st.number_input("Latitude", format="%.6f")
    longitude = st.number_input("Longitude", format="%.6f")

    if st.button("Salvar Plantação"):
        token = st.session_state.get("token")
        if token and cliente_id_plantacao:
            sucesso = inserir_plantacao_autenticada({
                "cliente_id": cliente_id_plantacao,
                "Cliente": cliente_nome_plantacao.split(" (ID")[0],  # extrai só o nome
                "cultura": cultura,
                "tipo_solo": tipo_solo,
                "Cidade": cidade,
                "Estado": estado,
                "latitude": latitude,
                "longitude": longitude
            }, token)
            if sucesso:
                st.success("✅ Plantação cadastrada com sucesso!")
            else:
                st.error("❌ Erro ao registrar a plantação.")
        else:
            st.warning("⚠️ Usuário não autenticado ou cliente inválido.")
else:
    st.info("ℹ️ Cadastre um cliente antes de cadastrar uma plantação.")
