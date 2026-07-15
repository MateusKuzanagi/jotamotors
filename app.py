import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Configurações da página
st.set_page_config(
    page_title="Sistema de Vendas & OS - Fechamento de Notinha",
    page_icon="📋",
    layout="wide"
)

# Estilização profissional para um visual moderno (inspirado no tema escuro/elegante)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .card {
        background-color: #1e222b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2d3139;
        margin-bottom: 20px;
    }
    .card-header {
        background-color: #1e222b;
        padding: 15px;
        border-radius: 8px 8px 0px 0px;
        border-bottom: 2px solid #2d3139;
        margin-bottom: 15px;
    }
    .info-title {
        font-size: 16px;
        font-weight: bold;
        color: #4ade80;
    }
    .total-highlight {
        font-size: 24px;
        font-weight: bold;
        color: #ef4444;
    }
    .badge-status {
        background-color: #103f29;
        color: #4ade80;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA (Session State)
# ---------------------------------------------------------
if 'clientes' not in st.session_state:
    st.session_state.clientes = [
        {"id": 1, "nome": "Carlos Silva", "moto": "XRE 300 (2012)", "placa": "OLT-9423"},
        {"id": 2, "nome": "Ana Souza", "moto": "CG 160 Fan (2020)", "placa": "ABC-1234"},
        {"id": 3, "nome": "Roberto Oliveira", "moto": "CB 500X (2022)", "placa": "XYZ-9876"}
    ]

if 'lancamentos' not in st.session_state:
    # Dados iniciais para exemplo com as novas colunas
    st.session_state.lancamentos = pd.DataFrame([
        {
            "Cliente ID": 1,
            "OS #": 5,
            "Data/Hora Entrada": "15/07/2026 10:00",
            "Data/Hora Saída": "15/07/2026 18:32",
            "Serviços & Peças de Reposição": "Troca de óleo",
            "Total Orçado (R$)": 120.00,
            "Total Pago (R$)": 0.00,
            "Forma de Pagamento": "Dinheiro"
        },
        {
            "Cliente ID": 1,
            "OS #": 6,
            "Data/Hora Entrada": "15/07/2026 10:00",
            "Data/Hora Saída": "15/07/2026 19:10",
            "Serviços & Peças de Reposição": "Pastilha de freio traseira",
            "Total Orçado (R$)": 85.00,
            "Total Pago (R$)": 0.00,
            "Forma de Pagamento": "Pix"
        },
        {
            "Cliente ID": 2,
            "OS #": 7,
            "Data/Hora Entrada": "15/07/2026 09:00",
            "Data/Hora Saída": "15/07/2026 14:00",
            "Serviços & Peças de Reposição": "Kit relação completo",
            "Total Orçado (R$)": 320.00,
            "Total Pago (R$)": 320.00,
            "Forma de Pagamento": "Cartão crédito"
        }
    ])

# ---------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------
st.title("📋 Fechamento de Notinha & Ordens de Serviço (OS)")

# Colunas de seleção de cliente e nova venda/OS
col_esquerda, col_direita = st.columns([1, 1])

with col_esquerda:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("👤 Passo 1: Selecionar Cliente")
    
    # Criar lista para selectbox
    lista_clientes = {c['id']: f"{c['nome']} — {c['moto']} ({c['placa']})" for c in st.session_state.clientes}
    cliente_selecionado_id = st.selectbox(
        "Selecione o Cliente para carregar a Notinha:",
        options=list(lista_clientes.keys()),
        format_func=lambda x: lista_clientes[x]
    )
    
    # Detalhes do cliente ativo
    cliente_ativo = next(c for c in st.session_state.clientes if c['id'] == cliente_selecionado_id)
    
    st.markdown(f"""
        <div style='background-color: #242933; padding: 12px; border-radius: 6px; margin-top: 10px;'>
            <strong>Moto Ativa:</strong> {cliente_ativo['moto']}<br>
            <strong>Placa:</strong> <span class='badge-status'>{cliente_ativo['placa']}</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_direita:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("➕ Passo 2: Registrar Novo Lançamento (Venda/OS)")
    
    with st.form("nova_os_form", clear_on_submit=True):
        servico = st.text_input("Descrição do Serviço / Peça", placeholder="Ex: Kit de Embreagem, Troca de Vela")
        
        # Novas colunas de Data/Hora de Entrada e Saída no formulário
        col_data1, col_data2 = st.columns(2)
        with col_data1:
            data_entrada_input = st.date_input("Data de Entrada", value=datetime.now().date())
            hora_entrada_input = st.time_input("Hora de Entrada", value=datetime.now().time())
        with col_data2:
            data_saida_input = st.date_input("Data de Saída", value=datetime.now().date())
            hora_saida_input = st.time_input("Hora de Saída", value=datetime.now().time())
            
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            valor_orcado = st.number_input("Valor Cobrado (R$)", min_value=0.0, step=10.0, value=0.0)
        with col_f2:
            valor_pago = st.number_input("Valor Pago Imediato (R$)", min_value=0.0, step=10.0, value=0.0)
            
        # Nova coluna de Forma de Pagamento
        forma_pagamento = st.selectbox(
            "Forma de Pagamento",
            options=["Dinheiro", "Pix", "Cartão débito", "Cartão crédito"]
        )
            
        salvar_os = st.form_submit_button("Adicionar à Conta do Cliente")
        
        if salvar_os:
            if servico.strip() == "":
                st.error("Por favor, informe a descrição do serviço ou peça.")
            else:
                # Combinar data e hora em string formatada
                entrada_str = f"{data_entrada_input.strftime('%d/%m/%Y')} {hora_entrada_input.strftime('%H:%M')}"
                saida_str = f"{data_saida_input.strftime('%d/%m/%Y')} {hora_saida_input.strftime('%H:%M')}"
                
                # Gerar ID para a nova OS
                novo_id_os = int(st.session_state.lancamentos["OS #"].max() + 1) if len(st.session_state.lancamentos) > 0 else 1
                nova_linha = pd.DataFrame([{
                    "Cliente ID": cliente_selecionado_id,
                    "OS #": novo_id_os,
                    "Data/Hora Entrada": entrada_str,
                    "Data/Hora Saída": saida_str,
                    "Serviços & Peças de Reposição": servico,
                    "Total Orçado (R$)": valor_orcado,
                    "Total Pago (R$)": valor_pago,
                    "Forma de Pagamento": forma_pagamento
                }])
                st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, nova_linha], ignore_index=True)
                st.success(f"Lançamento OS #{novo_id_os} registrado com sucesso!")
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# ÁREA DE EDIÇÃO DOS LANÇAMENTOS (INCLUINDO NOVAS FUNÇÕES)
# ---------------------------------------------------------
st.markdown("---")
st.subheader(f"🛠️ Lançamentos Ativos de: {cliente_ativo['nome']}")
st.info("💡 Você pode editar qualquer célula diretamente na tabela abaixo (incluindo as Datas, Horários, Forma de Pagamento, Valores, etc.)!")

# Filtrar lançamentos apenas do cliente selecionado
df_cliente = st.session_state.lancamentos[st.session_state.lancamentos["Cliente ID"] == cliente_selecionado_id].copy()

# Garantir que os campos numéricos estão corretos
df_cliente["Total Orçado (R$)"] = pd.to_numeric(df_cliente["Total Orçado (R$)"])
df_cliente["Total Pago (R$)"] = pd.to_numeric(df_cliente["Total Pago (R$)"])

# Tabela Editável utilizando st.data_editor
df_editado = st.data_editor(
    df_cliente,
    num_rows="dynamic",  # Permite adicionar (+) ou excluir lançamentos
    column_config={
        "Cliente ID": None,  # Oculta o ID do cliente da visualização do usuário
        "OS #": st.column_config.NumberColumn("OS #", disabled=True, format="%d"),
        "Data/Hora Entrada": st.column_config.TextColumn("Data/Hora Entrada"),
        "Data/Hora Saída": st.column_config.TextColumn("Data/Hora Saída"),
        "Serviços & Peças de Reposição": st.column_config.TextColumn("Descrição do Serviço / Peça", width="large"),
        "Total Orçado (R$)": st.column_config.NumberColumn("Total Orçado (R$)", min_value=0.0, format="R$ %.2f"),
        "Total Pago (R$)": st.column_config.NumberColumn("Valor Pago (R$)", min_value=0.0, format="R$ %.2f"),
        "Forma de Pagamento": st.column_config.SelectboxColumn(
            "Forma de Pagamento",
            options=["Dinheiro", "Pix", "Cartão débito", "Cartão crédito"],
            required=True
        )
    },
    use_container_width=True,
    key="editor_lancamentos"
)

# ---------------------------------------------------------
# ATUALIZAR O BANCO DE DADOS GLOBAL COM AS EDIÇÕES
# ---------------------------------------------------------
if not df_editado.equals(df_cliente):
    # Removemos os registros antigos deste cliente
    df_outros = st.session_state.lancamentos[st.session_state.lancamentos["Cliente ID"] != cliente_selecionado_id]
    
    # Garantimos que os registros novos mantêm o ID do cliente correto
    df_editado["Cliente ID"] = cliente_selecionado_id
    
    # Juntamos de volta no estado global
    st.session_state.lancamentos = pd.concat([df_outros, df_editado], ignore_index=True)
    st.rerun()

# ---------------------------------------------------------
# FECHAMENTO DA CONTA (CÁLCULO E NOTINHA)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("💰 Fechamento e Resumo de Valores")

# Cálculos com base nos valores editados
total_orcado = df_editado["Total Orçado (R$)"].sum() if len(df_editado) > 0 else 0.0
total_pago = df_editado["Total Pago (R$)"].sum() if len(df_editado) > 0 else 0.0
valor_em_aberto = total_orcado - total_pago

col_card1, col_card2, col_card3 = st.columns(3)

with col_card1:
    st.metric(label="Total de Serviços & Peças", value=f"R$ {total_orcado:,.2f}")
with col_card2:
    st.metric(label="Total Pago pelo Cliente", value=f"R$ {total_pago:,.2f}", delta="Já recebido", delta_color="normal")
with col_card3:
    status_cor = "inverse" if valor_em_aberto > 0 else "normal"
    st.metric(
        label="Valor Pendente / Em Aberto",
        value=f"R$ {valor_em_aberto:,.2f}",
        delta=f"Falta Receber R$ {valor_em_aberto:,.2f}" if valor_em_aberto > 0 else "Tudo Pago! ✅",
        delta_color=status_cor
    )

# Ações de Fechamento
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    # Gerar extrato atualizado com novas informações para impressão
    def gerar_extrato_txt(cliente, df_dados, total_o, total_p, total_a):
        output = io.StringIO()
        output.write(f"========= NOTINHA / EXTRATO DE OS =========\n")
        output.write(f"Cliente: {cliente['nome']}\n")
        output.write(f"Moto: {cliente['moto']} | Placa: {cliente['placa']}\n")
        output.write(f"Data de Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        output.write(f"============================================\n\n")
        output.write(f"Detalhamento de Lançamentos:\n")
        
        for index, row in df_dados.iterrows():
            output.write(f"OS #{int(row['OS #'])} | Entrada: {row['Data/Hora Entrada']} | Saída: {row['Data/Hora Saída']}\n")
            output.write(f" - {row['Serviços & Peças de Reposição']}\n")
            output.write(f" - Pagamento: {row['Forma de Pagamento']}\n")
            output.write(f" - Orçado: R$ {row['Total Orçado (R$)']:.2f} | Pago: R$ {row['Total Pago (R$)']:.2f}\n\n")
            
        output.write(f"============================================\n")
        output.write(f"TOTAL GERAL COBRADO: R$ {total_o:.2f}\n")
        output.write(f"TOTAL JÁ PAGO:       R$ {total_p:.2f}\n")
        output.write(f"VALOR EM ABERTO:     R$ {total_a:.2f}\n")
        output.write(f"============================================\n")
        output.write(f"Agradecemos a preferência! Volte sempre.\n")
        return output.getvalue()

    extrato_conteudo = gerar_extrato_txt(cliente_ativo, df_editado, total_orcado, total_pago, valor_em_aberto)
    
    st.download_button(
        label="🖨️ Exportar Extrato Completo",
        data=extrato_conteudo,
        file_name=f"notinha_{cliente_ativo['nome'].lower().replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True
    )

with col_btn2:
    if st.button("✅ Quitar Tudo e Fechar Conta", use_container_width=True, type="primary"):
        st.session_state.lancamentos.loc[st.session_state.lancamentos["Cliente ID"] == cliente_selecionado_id, "Total Pago (R$)"] = \
            st.session_state.lancamentos.loc[st.session_state.lancamentos["Cliente ID"] == cliente_selecionado_id, "Total Orçado (R$)"]
        st.success(f"Conta de {cliente_ativo['nome']} quitada com sucesso!")
        st.rerun()
