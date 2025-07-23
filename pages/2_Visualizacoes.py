import streamlit as st
from supabase_utils import (
    carregar_clientes1,
    carregar_vendas1,
    carregar_itens_venda1,
    carregar_plantacoes1,
    carregar_produtos1,
    excluir_cliente,
    excluir_vendas_por_cliente,  # nova função para excluir vendas do cliente
    requer_autenticacao,excluir_itens_venda_por_cliente,
    excluir_plantacoes_por_cliente,restore_from_cookie  # nova função para excluir plantações do cliente
)

st.title("🧾 Visualizar Últimos Registros")
restore_from_cookie()
requer_autenticacao()
token = st.session_state.get("token")
st.subheader("Clientes")
st.dataframe(carregar_clientes1(token=token))

st.subheader("Vendas")
st.dataframe(carregar_vendas1(token=token))

st.subheader("Itens de Venda")
st.dataframe(carregar_itens_venda1(token=token))

st.subheader("Plantação")
st.dataframe(carregar_plantacoes1(token=token))

st.subheader("Produtos")
st.dataframe(carregar_produtos1(token=token))
st.markdown("---")
st.subheader("🗑️ Excluir Histórico de Cliente")

clientes_atualizados = carregar_clientes1(token=token)
if not clientes_atualizados.empty:
    cliente_selecionado = st.selectbox(
        "Selecione um cliente para excluir:",
        clientes_atualizados[["cliente_id", "Cliente"]].apply(
            lambda row: f"{row['cliente_id']} - {row['Cliente']}", axis=1
        )
    )

    confirmar_exclusao = st.checkbox("⚠️ Confirmo que desejo excluir este cliente e todos os dados relacionados")

    if st.button("Excluir Histórico") and confirmar_exclusao:
        id_excluir = int(cliente_selecionado.split(" - ")[0])

        # 🔁 Etapas da exclusão
        try:
            sucesso_itens = excluir_itens_venda_por_cliente(id_excluir)
            sucesso_vendas = excluir_vendas_por_cliente(id_excluir)
            sucesso_plantacoes = excluir_plantacoes_por_cliente(id_excluir)
            sucesso_cliente = excluir_cliente(id_excluir)

            if sucesso_cliente:
                st.success("✅ Cliente e todos os dados relacionados foram excluídos com sucesso!")
                st.rerun()
            else:
                st.error("❌ Erro ao excluir cliente.")
        except Exception as e:
            st.error(f"❌ Erro durante a exclusão: {e}")

    elif not confirmar_exclusao:
        st.warning("⚠️ Você precisa confirmar a exclusão marcando a caixa acima.")
else:
    st.info("ℹ️ Nenhum cliente disponível para exclusão.")
