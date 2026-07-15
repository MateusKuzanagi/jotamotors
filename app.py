import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Gerenciador de Ordens de Serviço",
    page_icon="🏍️",
    layout="wide"
)

# Estilização CSS personalizada para simular o tema escuro/elegante da imagem
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .card-header {
        background-color: #1e222b;
        padding: 15px;
        border-radius: 8px 8px 0px 0px;
        border-bottom: 2px solid #2d3139;
        margin-bottom: 0px;
    }
    .info-text {
        font-size: 14px;
        color: #e0e0e0;
        margin-bottom: 5px;
    }
    .badge-placa {
        background-color: #103f29;
        color: #4ade80;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏍️ Sistema de Controle de Oficina")

# 1. ESTADO DA APLICAÇÃO (Banco de dados temporário em memória)
if 'moto_info' not in st.session_state:
    st.session_state.moto_info = {
        "modelo": "XRE 300",
        "ano": 2012,
        "placa": "OLT-9423",
        "km_entrada": 12500,
        "km_saida": 12505,
        "data_entrada": datetime(2026, 7, 15).date(),
        "data_saida": datetime(2026, 7, 15).date()
    }

if 'dados_os' not in st.session_state:
    # Dados iniciais da tabela baseados na sua imagem
    st.session_state.dados_os = pd.DataFrame([
        {
            "OS #": 5,
            "Data da OS": "15/07/2026 18:32",
            "Serviços & Peças de Reposição": "Troca de óleo",
            "Total Orçado (R$)": 120.00,
            "Total Pago (R$)": 100.00
        }
    ])

# 2. CABEÇALHO INFORMATIVO (EDITÁVEL)
st.markdown("### 📝 Informações Gerais da Ordem de Serviço")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.session_state.moto_info["modelo"] = st.text_input("Moto Registrada", st.session_state.moto_info["modelo"])
with col2:
    st.session_state.moto_info["ano"] = st.number_input("Ano", value=st.session_state.moto_info["ano"], step=1)
with col3:
    st.session_state.moto_info["placa"] = st.text_input("Placa", st.session_state.moto_info["placa"])
with col4:
    km_in = st.text_input("KM Entrada", value=str(st.session_state.moto_info["km_entrada"]))
    km_out = st.text_input("KM Saída", value=str(st.session_state.moto_info["km_saida"]))

# Exibição estilizada do cabeçalho atualizado
st.markdown(f"""
<div class="card-header">
    <div class="info-text">
        <strong>🏍️ Moto Registrada:</strong> {st.session_state.moto_info['modelo']} (Ano: {st.session_state.moto_info['ano']}) | 
        <strong>Placa:</strong> <span class="badge-placa">{st.session_state.moto_info['placa']}</span>
    </div>
    <div class="info-text" style="margin-top: 8px;">
        📍 <strong>KM Entrada / Saída:</strong> {km_in} / {km_out} | 
        📅 <strong>Entrada/Saída Oficina:</strong> {st.session_state.moto_info['data_entrada'].strftime('%d/%m/%Y')} a {st.session_state.moto_info['data_saida'].strftime('%d/%m/%Y')}
    </div>
</div>
""", unsafe_allow_html=True)

# 3. TABELA INTERATIVA E EDITÁVEL (Total Orçado, Pago e cálculo de Valor em Aberto)
st.markdown("### 🛠️ Detalhes dos Serviços e Valores")
st.caption("Dica: Dê um duplo clique em qualquer célula da tabela abaixo para editar os valores diretamente!")

# Criamos uma cópia dos dados para edição
df_para_editar = st.session_state.dados_os.copy()

# Garantimos os tipos numéricos para os cálculos
df_para_editar["Total Orçado (R$)"] = pd.to_numeric(df_para_editar["Total Orçado (R$)"])
df_para_editar["Total Pago (R$)"] = pd.to_numeric(df_para_editar["Total Pago (R$)"])

# st.data_editor permite editar os dados diretamente na tela de forma elegante
df_editado = st.data_editor(
    df_para_editar,
    num_rows="dynamic", # Permite que você adicione novas linhas clicando no "+"
    column_config={
        "OS #": st.column_config.NumberColumn("OS #", disabled=True, format="%d"),
        "Data da OS": st.column_config.TextColumn("Data da OS"),
        "Serviços & Peças de Reposição": st.column_config.TextColumn("Serviços & Peças de Reposição", width="medium"),
        "Total Orçado (R$)": st.column_config.NumberColumn("Total Orçado (R$)", min_value=0.0, format="R$ %.2f"),
        "Total Pago (R$)": st.column_config.NumberColumn("Total Pago (R$)", min_value=0.0, format="R$ %.2f")
    },
    use_container_width=True,
    key="os_editor"
)

# Atualiza o estado da aplicação com os dados novos editados pelo usuário
st.session_state.dados_os = df_editado

# 4. CÁLCULO DE VALORES EM ABERTO E RESUMO FINACEIRO
# Calculamos os totais gerais
total_orcado_geral = df_editado["Total Orçado (R$)"].sum()
total_pago_geral = df_editado["Total Pago (R$)"].sum()
total_em_aberto = total_orcado_geral - total_pago_geral

# Exibe os cartões com os resultados
st.markdown("### 📊 Resumo Financeiro")
col_res1, col_res2, col_res3 = st.columns(3)

with col_res1:
    st.metric(label="Total Orçado", value=f"R$ {total_orcado_geral:,.2f}")
with col_res2:
    st.metric(label="Total Pago", value=f"R$ {total_pago_geral:,.2f}", delta=f"Pago", delta_color="normal")
with col_res3:
    # Mostra em vermelho se houver valor em aberto
    cor_alerta = "inverse" if total_em_aberto > 0 else "normal"
    st.metric(
        label="Valor em Aberto (Restante)", 
        value=f"R$ {total_em_aberto:,.2f}", 
        delta=f"- R$ {total_em_aberto:,.2f}" if total_em_aberto > 0 else "Tudo Pago!",
        delta_color=cor_alerta
    )

# 5. GERADOR DE EXTRATO EM PDF (Botão de Exportação)
def gerar_pdf_mock(moto_info, df_dados, total_o, total_p, total_a):
    # Função simples para gerar um relatório em texto amigável ou CSV para download
    # Para simplificar e rodar direto no GitHub Pages/Streamlit sem dependências complexas de OS
    output = io.StringIO()
    output.write(f"EXTRATO DE ORDEM DE SERVIÇO\n")
    output.write(f"="*40 + "\n")
    output.write(f"Moto: {moto_info['modelo']} ({moto_info['ano']}) - Placa: {moto_info['placa']}\n")
    output.write(f"KM Entrada/Saída: {km_in} / {km_out}\n")
    output.write(f"Data de Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    output.write(f"="*40 + "\n\n")
    
    output.write("SERVIÇOS:\n")
    for index, row in df_dados.iterrows():
        output.write(f"- OS #{row['OS #']} | {row['Serviços & Peças de Reposição']} | Orçado: R$ {row['Total Orçado (R$)']:.2f} | Pago: R$ {row['Total Pago (R$)']:.2f}\n")
        
    output.write(f"\n" + "="*40 + "\n")
    output.write(f"TOTAL ORÇADO: R$ {total_o:.2f}\n")
    output.write(f"TOTAL PAGO: R$ {total_p:.2f}\n")
    output.write(f"VALOR EM ABERTO: R$ {total_a:.2f}\n")
    output.write(f"="*40 + "\n")
    return output.getvalue()

extrato_txt = gerar_pdf_mock(
    st.session_state.moto_info, 
    df_editado, 
    total_orcado_geral, 
    total_pago_geral, 
    total_em_aberto
)

# Botão de exportação semelhante ao da sua imagem
st.download_button(
    label="🖨️ Exportar Extrato Completo (TXT/Relatório)",
    data=extrato_txt,
    file_name=f"extrato_{st.session_state.moto_info['placa']}.txt",
    mime="text/plain"
)
