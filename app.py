import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuração da página do site
st.set_page_config(
    page_title="JotaMotors - Oficina Mecânica (Google Sheets)",
    page_icon="🏍️",
    layout="wide"
)

# Identidade Visual do JotaMotors
COR_BG = "#0f172a"          
COR_CARD = "#1e293b"        
COR_HEADER = "#020617"      
COR_TEXT = "#f8fafc"        
COR_TEXT_MUTED = "#94a3b8"  
COR_ACCENT_BLUE = "#3b82f6" 
COR_ACCENT_CYAN = "#06b6d4" 
COR_ACCENT_GREEN = "#10b981"
COR_ACCENT_RED = "#ef4444"  

# ==========================================
# CSS CUSTOMIZADO PARA CORRIGIR O LAYOUT
# ==========================================
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
    div.stButton > button {
        background-color: #06b6d4 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #0891b2 !important;
        transform: translateY(-1px);
    }
    div.stButton > button[key*="excluir"] {
        background-color: #ef4444 !important;
    }
    div.stButton > button[key*="excluir"]:hover {
        background-color: #dc2626 !important;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        border-color: #334155 !important;
        border-radius: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXÃO COM GOOGLE SHEETS
# ==========================================
# Para este código funcionar, você deve configurar o arquivo .streamlit/secrets.toml
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro ao conectar com o Google Sheets. Verifique suas credenciais em .streamlit/secrets.toml")
    st.stop()

# Funções auxiliares para leitura e escrita de abas
def carregar_aba(nome_aba):
    try:
        df = conn.read(worksheet=nome_aba, ttl="1m")
        # Remover colunas ou linhas totalmente vazias que o Sheets às vezes gera
        df = df.dropna(how='all')
        return df
    except Exception:
        # Se a aba não existir, retorna um DataFrame vazio com colunas padrão
        if nome_aba == "Produtos":
            return pd.DataFrame(columns=["ID", "NomeProduto", "Descricao", "Preco", "QtdEstoque"])
        elif nome_aba == "Clientes":
            return pd.DataFrame(columns=["ID", "Nome", "Endereco", "Telefone", "ModeloMoto", "AnoMoto", "KMEntrada", "KMSaida", "DataEntrada", "DataSaida", "Placa"])
        elif nome_aba == "Vendas":
            return pd.DataFrame(columns=["ID", "ClienteID", "Servico", "ValorTotal", "ValorPago", "DataCompra", "DataHoraEntrada", "DataHoraSaida", "FormaPagamento", "Observacoes"])
        return pd.DataFrame()

def salvar_aba(nome_aba, df):
    conn.update(worksheet=nome_aba, data=df)

# ==========================================
# GERAÇÃO DE CÓDIGO E ID SEQUENCIAIS
# ==========================================
def proximo_id_produto(df_prod):
    if df_prod.empty or "ID" not in df_prod.columns:
        return "PRD-0001"
    ids = df_prod["ID"].astype(str).tolist()
    numeros = []
    for i in ids:
        if i.startswith("PRD-") and i[4:].isdigit():
            numeros.append(int(i[4:]))
    proximo = max(numeros) + 1 if numeros else 1
    return f"PRD-{proximo:04d}"

def proximo_id_numerico(df, coluna="ID"):
    if df.empty or coluna not in df.columns:
        return 1
    # Converte para numérico e pega o maior
    valores = pd.to_numeric(df[coluna], errors='coerce').dropna()
    if valores.empty:
        return 1
    return int(valores.max() + 1)

# ==========================================
# CONTROLE DE SESSÃO E LOGIN
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ""

usuarios_validos = {
    "admin": "123",
    "maironxd": "14125",
    "luana": "14125",
    "josue": "123"
}

if not st.session_state['logged_in']:
    st.write("")
    st.write("")
    st.write("")
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown("<h1 style='text-align: center; color: #06b6d4; margin-bottom: 0px;'>🔑 JotaMotors ERP</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 20px;'>Planilhas do Google & AppSheet Integrados</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            with st.form("login_form"):
                user_input = st.text_input("Usuário")
                pass_input = st.text_input("Senha", type="password")
                entrar = st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True)
                if entrar:
                    if user_input.strip() in usuarios_validos and usuarios_validos[user_input.strip()] == pass_input.strip():
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = user_input.strip()
                        st.success("Acesso autorizado! Carregando...")
                        st.rerun()
                    else:
                        st.error("Usuário ou Senha incorretos!")
    st.stop()

# ==========================================
# NAVEGAÇÃO E INTERFACE PRINCIPAL
# ==========================================
st.sidebar.markdown(f"### 👤 Usuário: **{st.session_state['user']}**")
if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
    st.session_state['logged_in'] = False
    st.session_state['user'] = ""
    st.rerun()

st.sidebar.divider()
menu = st.sidebar.radio(
    "Navegação do Sistema",
    ["📊 Dashboard & Estoque", "👥 Gestão de Clientes", "📈 Desempenho do Mês"]
)

col_logo, _ = st.columns([2, 1])
with col_logo:
    st.markdown("<h1 style='color: #06b6d4; margin-bottom: 0px; padding-bottom:0px;'>JotaMotors</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 13px; margin-top:0px;'>SISTEMA INTEGRADO COM GOOGLE SHEETS</p>", unsafe_allow_html=True)

st.divider()

# ==========================================
# CARREGAMENTO DOS DADOS DO GOOGLE SHEETS
# ==========================================
df_produtos = carregar_aba("Produtos")
df_clientes = carregar_aba("Clientes")
df_vendas = carregar_aba("Vendas")

# Garantir tipos de dados corretos para as operações
if not df_produtos.empty:
    df_produtos["Preco"] = pd.to_numeric(df_produtos["Preco"], errors="coerce").fillna(0.0)
    df_produtos["QtdEstoque"] = pd.to_numeric(df_produtos["QtdEstoque"], errors="coerce").fillna(0).astype(int)

if not df_vendas.empty:
    df_vendas["ValorTotal"] = pd.to_numeric(df_vendas["ValorTotal"], errors="coerce").fillna(0.0)
    df_vendas["ValorPago"] = pd.to_numeric(df_vendas["ValorPago"], errors="coerce").fillna(0.0)

# ==========================================
# ABA 1: DASHBOARD & ESTOQUE
# ==========================================
if menu == "📊 Dashboard & Estoque":
    # Estatísticas do estoque e faturamento do mês atual
    total_produtos = len(df_produtos)
    total_itens = df_produtos["QtdEstoque"].sum() if not df_produtos.empty else 0
    valor_estoque = (df_produtos["Preco"] * df_produtos["QtdEstoque"]).sum() if not df_produtos.empty else 0.0
    estoque_baixo = len(df_produtos[df_produtos["QtdEstoque"] <= 3]) if not df_produtos.empty else 0
    
    # Faturamento no mês atual (baseado em DataCompra com formato DD/MM/AAAA)
    mes_atual = datetime.now().strftime("/%m/%Y")
    if not df_vendas.empty and "DataCompra" in df_vendas.columns:
        filtro_mes = df_vendas["DataCompra"].astype(str).str.contains(mes_atual, na=False)
        lucro_mes = df_vendas.loc[filtro_mes, "ValorPago"].sum()
    else:
        lucro_mes = 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.metric("📦 Cadastrados / Total Itens", f"{total_produtos} ref", f"{total_itens} un")
    with col2:
        with st.container(border=True):
            st.metric("💰 Custo total do Estoque", f"R$ {valor_estoque:,.2f}")
    with col3:
        with st.container(border=True):
            st.metric("📈 Faturamento do Mês", f"R$ {lucro_mes:,.2f}")
    with col4:
        with st.container(border=True):
            st.metric("⚠️ Alerta Estoque Baixo", f"{estoque_baixo} itens", delta="- Crítico" if estoque_baixo > 0 else "OK", delta_color="inverse")

    st.write("")
    st.subheader("📦 Consulta de Estoque de Peças (Sincronizado com Google Sheets)")
    
    busca_prod = st.text_input("🔎 Digite para pesquisar produto (Código ou Nome):", placeholder="Buscar por código ou nome do produto...")
    
    df_exibicao_prod = df_produtos.copy()
    if busca_prod and not df_exibicao_prod.empty:
        df_exibicao_prod = df_exibicao_prod[
            df_exibicao_prod['ID'].astype(str).str.contains(busca_prod, case=False) | 
            df_exibicao_prod['NomeProduto'].astype(str).str.contains(busca_prod, case=False)
        ]
    
    st.dataframe(df_exibicao_prod, use_container_width=True, hide_index=True)

    col_cad, col_ed = st.columns(2)

    with col_cad:
        st.markdown("### ➕ Novo Cadastro")
        sugestao_codigo = proximo_id_produto(df_produtos)
        
        with st.container(border=True):
            with st.form("form_add_prod", clear_on_submit=True):
                new_cod = st.text_input("Código/ID do Produto (Automático)*", value=sugestao_codigo)
                new_nome = st.text_input("Nome do Produto*")
                new_desc = st.text_input("Descrição")
                new_preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=0.01)
                new_qtd = st.number_input("Quantidade Inicial em Estoque", min_value=0, step=1, value=0)
                
                salvar_novo = st.form_submit_button("CADASTRAR PRODUTO", use_container_width=True)
                if salvar_novo:
                    if not new_cod.strip() or not new_nome.strip():
                        st.warning("Código e Nome são obrigatórios!")
                    elif not df_produtos.empty and new_cod.strip().upper() in df_produtos["ID"].astype(str).values:
                        st.error("Este Código/ID já existe na planilha do Google Sheets!")
                    else:
                        novo_item = pd.DataFrame([{
                            "ID": new_cod.strip().upper(),
                            "NomeProduto": new_nome.strip(),
                            "Descricao": new_desc.strip(),
                            "Preco": new_preco,
                            "QtdEstoque": int(new_qtd)
                        }])
                        df_atualizado = pd.concat([df_produtos, novo_item], ignore_index=True)
                        salvar_aba("Produtos", df_atualizado)
                        st.success("Produto gravado no Google Sheets!")
                        st.rerun()

    with col_ed:
        st.markdown("### ✏️ Modificar Produto")
        with st.container(border=True):
            prod_ids = df_produtos["ID"].astype(str).tolist() if not df_produtos.empty else []
            selected_prod_id = st.selectbox("Escolha um produto para editar", [""] + prod_ids)
            
            if selected_prod_id:
                idx_prod = df_produtos[df_produtos["ID"] == selected_prod_id].index[0]
                selected_prod = df_produtos.loc[idx_prod]
                
                with st.form("form_edit_prod"):
                    st.info(f"Editando Produto: {selected_prod['ID']}")
                    edit_nome = st.text_input("Nome do Produto", value=selected_prod['NomeProduto'])
                    edit_desc = st.text_input("Descrição", value=str(selected_prod['Descricao']) if pd.notna(selected_prod['Descricao']) else "")
                    edit_preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=0.01, value=float(selected_prod['Preco']))
                    edit_qtd = st.number_input("Quantidade em Estoque", min_value=0, step=1, value=int(selected_prod['QtdEstoque']))
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        btn_salvar = st.form_submit_button("💾 SALVAR", use_container_width=True)
                    with col_btn2:
                        btn_excluir = st.form_submit_button("🗑️ EXCLUIR", use_container_width=True)
                        
                    if btn_salvar:
                        if not edit_nome.strip():
                            st.warning("O nome não pode ser vazio!")
                        else:
                            df_produtos.at[idx_prod, "NomeProduto"] = edit_nome.strip()
                            df_produtos.at[idx_prod, "Descricao"] = edit_desc.strip()
                            df_produtos.at[idx_prod, "Preco"] = edit_preco
                            df_produtos.at[idx_prod, "QtdEstoque"] = int(edit_qtd)
                            salvar_aba("Produtos", df_produtos)
                            st.success("Produto atualizado no Google Sheets!")
                            st.rerun()
                            
                    if btn_excluir:
                        df_produtos = df_produtos.drop(idx_prod)
                        salvar_aba("Produtos", df_produtos)
                        st.success("Produto removido do Google Sheets!")
                        st.rerun()

# ==========================================
# ABA 2: GESTÃO DE CLIENTES
# ==========================================
elif menu == "👥 Gestão de Clientes":
    st.subheader("👥 Fichas de Clientes e Ordens de Serviços")
    
    busca_cli = st.text_input("🔎 Pesquisar Ficha de Clientes (Nome, Modelo ou Placa da Moto):", placeholder="Ex: Honda CG, João, ABC1D23...")
    df_exibicao_cli = df_clientes.copy()
    
    if busca_cli and not df_exibicao_cli.empty:
        df_exibicao_cli = df_exibicao_cli[
            df_exibicao_cli['Nome'].astype(str).str.contains(busca_cli, case=False) |
            df_exibicao_cli['ModeloMoto'].astype(str).str.contains(busca_cli, case=False) |
            df_exibicao_cli['Placa'].astype(str).str.contains(busca_cli, case=False)
        ]
        
    st.dataframe(df_exibicao_cli, use_container_width=True, hide_index=True)

    st.divider()
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("### ➕ Cadastrar Novo Cliente")
        with st.container(border=True):
            with st.form("form_add_cli", clear_on_submit=True):
                c_nome = st.text_input("Nome do Cliente*")
                c_end = st.text_input("Endereço")
                c_tel = st.text_input("Telefone")
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    c_mod = st.text_input("Modelo da Moto")
                    c_pla = st.text_input("Placa da Moto")
                    c_kme = st.text_input("KM de Entrada")
                    c_dent = st.text_input("Entrada (DD/MM/AAAA)")
                with col_m2:
                    c_ano = st.text_input("Ano da Moto")
                    st.write("")  
                    c_kms = st.text_input("KM de Saída")
                    c_dsai = st.text_input("Saída (DD/MM/AAAA)")
                
                st.write("")
                gravar_cli = st.form_submit_button("GRAVAR FICHA DO CLIENTE", use_container_width=True)
                if gravar_cli:
                    if not c_nome.strip():
                        st.warning("Nome do cliente é obrigatório!")
                    else:
                        prox_id = proximo_id_numerico(df_clientes, "ID")
                        novo_cli = pd.DataFrame([{
                            "ID": prox_id,
                            "Nome": c_nome.strip(),
                            "Endereco": c_end.strip(),
                            "Telefone": c_tel.strip(),
                            "ModeloMoto": c_mod.strip(),
                            "AnoMoto": c_ano.strip(),
                            "KMEntrada": c_kme.strip(),
                            "KMSaida": c_kms.strip(),
                            "DataEntrada": c_dent.strip(),
                            "DataSaida": c_dsai.strip(),
                            "Placa": c_pla.strip().upper()
                        }])
                        df_atualizado = pd.concat([df_clientes, novo_cli], ignore_index=True)
                        salvar_aba("Clientes", df_atualizado)
                        st.success("Cliente salvo com sucesso no Google Sheets!")
                        st.rerun()

        st.markdown("### 🛠️ Registrar Ordem de Serviço (Venda)")
        with st.container(border=True):
            cli_dict = {f"{row['Nome']} (ID: {row['ID']})": row['ID'] for _, row in df_clientes.iterrows()} if not df_clientes.empty else {}
            sel_cli_venda = st.selectbox("Escolha o Cliente para associar a OS", [""] + list(cli_dict.keys()))
            
            if sel_cli_venda:
                target_cli_id = cli_dict[sel_cli_venda]
                with st.form("form_lancar_os", clear_on_submit=True):
                    os_desc = st.text_input("Serviços Realizados / Peças Trocadas*")
                    
                    col_dt_e, col_dt_s = st.columns(2)
                    with col_dt_e:
                        os_dt_entrada = st.date_input("Data de Entrada", value=datetime.now().date())
                        os_hr_entrada = st.time_input("Horário de Entrada", value=datetime.now().time())
                    with col_dt_s:
                        os_dt_saida = st.date_input("Data de Saída", value=datetime.now().date())
                        os_hr_saida = st.time_input("Horário de Saída", value=datetime.now().time())

                    col_os1, col_os2 = st.columns(2)
                    with col_os1:
                        os_total = st.number_input("Valor Total do Orçamento (R$)", min_value=0.0, step=0.01)
                    with col_os2:
                        os_pago = st.number_input("Valor Pago de Adiantamento (R$)", min_value=0.0, step=0.01)
                    
                    os_forma_pagamento = st.selectbox("Forma de Pagamento", options=["Dinheiro", "Pix", "Cartão débito", "Cartão crédito"])
                    os_obs_extra = st.text_area("Anotação / Observação Extra para o Cliente")

                    st.write("")
                    gravar_os = st.form_submit_button("LANÇAR ORDEM DE SERVIÇO", use_container_width=True)
                    if gravar_os:
                        if not os_desc.strip():
                            st.warning("A descrição da OS é obrigatória!")
                        else:
                            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                            entrada_completa = f"{os_dt_entrada.strftime('%d/%m/%Y')} {os_hr_entrada.strftime('%H:%M')}"
                            saida_completa = f"{os_dt_saida.strftime('%d/%m/%Y')} {os_hr_saida.strftime('%H:%M')}"
                            
                            prox_id_venda = proximo_id_numerico(df_vendas, "ID")
                            nova_os = pd.DataFrame([{
                                "ID": prox_id_venda,
                                "ClienteID": target_cli_id,
                                "Servico": os_desc.strip(),
                                "ValorTotal": os_total,
                                "ValorPago": os_pago,
                                "DataCompra": data_atual,
                                "DataHoraEntrada": entrada_completa,
                                "DataHoraSaida": saida_completa,
                                "FormaPagamento": os_forma_pagamento,
                                "Observacoes": os_obs_extra.strip()
                            }])
                            df_atualizado = pd.concat([df_vendas, nova_os], ignore_index=True)
                            salvar_aba("Vendas", df_atualizado)
                            st.success("Ordem de serviço registrada no Google Sheets!")
                            st.rerun()

    with col_c2:
        st.markdown("### ✏️ Alterar ou Remover Cliente")
        with st.container(border=True):
            cli_dict_ed = {f"{row['Nome']} (ID: {row['ID']})": row['ID'] for _, row in df_clientes.iterrows()} if not df_clientes.empty else {}
            sel_cli_ed = st.selectbox("Escolha o cliente para atualizar", [""] + list(cli_dict_ed.keys()))
            
            if sel_cli_ed:
                target_cli_id = cli_dict_ed[sel_cli_ed]
                idx_cli = df_clientes[df_clientes["ID"] == target_cli_id].index[0]
                c_info = df_clientes.loc[idx_cli]
                
                with st.form("form_edit_cli"):
                    ec_nome = st.text_input("Nome Completo", value=c_info["Nome"])
                    ec_end = st.text_input("Endereço Completo", value=str(c_info["Endereco"]) if pd.notna(c_info["Endereco"]) else "")
                    ec_tel = st.text_input("Telefone de Contato", value=str(c_info["Telefone"]) if pd.notna(c_info["Telefone"]) else "")
                    
                    col_me1, col_me2 = st.columns(2)
                    with col_me1:
                        ec_mod = st.text_input("Modelo da Moto", value=str(c_info["ModeloMoto"]) if pd.notna(c_info["ModeloMoto"]) else "")
                        ec_pla = st.text_input("Placa da Moto", value=str(c_info["Placa"]) if pd.notna(c_info["Placa"]) else "")  
                        ec_kme = st.text_input("KM Entrada", value=str(c_info["KMEntrada"]) if pd.notna(c_info["KMEntrada"]) else "")
                        ec_dent = st.text_input("Data Entrada", value=str(c_info["DataEntrada"]) if pd.notna(c_info["DataEntrada"]) else "")
                    with col_me2:
                        ec_ano = st.text_input("Ano Moto", value=str(c_info["AnoMoto"]) if pd.notna(c_info["AnoMoto"]) else "")
                        st.write("")  
                        ec_kms = st.text_input("KM Saída", value=str(c_info["KMSaida"]) if pd.notna(c_info["KMSaida"]) else "")
                        ec_dsai = st.text_input("Data Saída", value=str(c_info["DataSaida"]) if pd.notna(c_info["DataSaida"]) else "")
                    
                    st.write("")
                    col_bcli1, col_bcli2 = st.columns(2)
                    with col_bcli1:
                        submit_edit_cli = st.form_submit_button("💾 ATUALIZAR", use_container_width=True)
                    with col_bcli2:
                        submit_del_cli = st.form_submit_button("🗑️ EXCLUIR CLIENTE", use_container_width=True)
                        
                    if submit_edit_cli:
                        if not ec_nome.strip():
                            st.warning("O Nome é obrigatório!")
                        else:
                            df_clientes.at[idx_cli, "Nome"] = ec_nome.strip()
                            df_clientes.at[idx_cli, "Endereco"] = ec_end.strip()
                            df_clientes.at[idx_cli, "Telefone"] = ec_tel.strip()
                            df_clientes.at[idx_cli, "ModeloMoto"] = ec_mod.strip()
                            df_clientes.at[idx_cli, "AnoMoto"] = ec_ano.strip()
                            df_clientes.at[idx_cli, "KMEntrada"] = ec_kme.strip()
                            df_clientes.at[idx_cli, "KMSaida"] = ec_kms.strip()
                            df_clientes.at[idx_cli, "DataEntrada"] = ec_dent.strip()
                            df_clientes.at[idx_cli, "DataSaida"] = ec_dsai.strip()
                            df_clientes.at[idx_cli, "Placa"] = ec_pla.strip().upper()
                            
                            salvar_aba("Clientes", df_clientes)
                            st.success("Ficha atualizada no Google Sheets!")
                            st.rerun()
                            
                    if submit_del_cli:
                        # Remove o cliente e suas OS vinculadas
                        df_clientes = df_clientes.drop(idx_cli)
                        if not df_vendas.empty:
                            df_vendas = df_vendas[df_vendas["ClienteID"] != target_cli_id]
                            salvar_aba("Vendas", df_vendas)
                        salvar_aba("Clientes", df_clientes)
                        st.success("Cliente e OSs associadas removidas!")
                        st.rerun()

    # Histórico de Serviços / Gerador de Extrato
    st.divider()
    st.subheader("📜 Extrato e Histórico de Prontuários")
    
    cli_dict_h = {f"{row['Nome']} (ID: {row['ID']})": row['ID'] for _, row in df_clientes.iterrows()} if not df_clientes.empty else {}
    sel_cli_hist = st.selectbox("Selecione o Cliente para detalhar o extrato financeiro", [""] + list(cli_dict_h.keys()))
    
    if sel_cli_hist:
        cli_id_h = cli_dict_h[sel_cli_hist]
        
        # Filtra histórico de vendas do cliente
        historico = df_vendas[df_vendas["ClienteID"].astype(str) == str(cli_id_h)] if not df_vendas.empty else pd.DataFrame()
        cli_meta = df_clientes[df_clientes["ID"] == cli_id_h].iloc[0]
        
        with st.container(border=True):
            st.markdown(f"🏍️ **Moto registrada:** {cli_meta['ModeloMoto'] or 'Não cadastrada'} (Ano: {cli_meta['AnoMoto'] or 'N/A'}) | **Placa:** `{cli_meta['Placa'] or 'N/A'}`")
            st.markdown(f"📍 **KM Entrada / Saída:** `{cli_meta['KMEntrada'] or '-'}` / `{cli_meta['KMSaida'] or '-'}` | **Entrada/Saída Oficina:** {cli_meta['DataEntrada'] or '-'} a {cli_meta['DataSaida'] or '-'}")
            
            if not historico.empty:
                st.dataframe(historico, use_container_width=True, hide_index=True)
                
                st.markdown("### ✏️ Editar ou Excluir Lançamento (OS)")
                os_dict = {f"OS #{row['ID']} - {row['Servico']}"[:50] + "...": row['ID'] for _, row in historico.iterrows()}
                sel_os_ed = st.selectbox("Selecione a Ordem de Serviço que deseja alterar ou excluir:", [""] + list(os_dict.keys()))
                
                if sel_os_ed:
                    os_id_target = os_dict[sel_os_ed]
                    idx_os = df_vendas[df_vendas["ID"] == os_id_target].index[0]
                    cur_os = df_vendas.loc[idx_os]
                    
                    with st.form("form_edit_os"):
                        st.info(f"Alterando OS #{os_id_target}")
                        edit_servico = st.text_input("Serviços & Peças de Reposição", value=cur_os['Servico'])
                        
                        col_v1, col_v2 = st.columns(2)
                        with col_v1:
                            edit_vtotal = st.number_input("Total Orçado (R$)", value=float(cur_os['ValorTotal']), step=0.01)
                        with col_v2:
                            edit_vpago = st.number_input("Total Pago (R$)", value=float(cur_os['ValorPago']), step=0.01)

                        col_dt1, col_dt2 = st.columns(2)
                        with col_dt1:
                            edit_ent = st.text_input("Entrada Oficial", value=str(cur_os['DataHoraEntrada']) if pd.notna(cur_os['DataHoraEntrada']) else "")
                        with col_dt2:
                            edit_sai = st.text_input("Saída Oficial", value=str(cur_os['DataHoraSaida']) if pd.notna(cur_os['DataHoraSaida']) else "")

                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            opcoes_pgto = ["Dinheiro", "Pix", "Cartão débito", "Cartão crédito"]
                            idx_pgto = opcoes_pgto.index(cur_os['FormaPagamento']) if cur_os['FormaPagamento'] in opcoes_pgto else 0
                            edit_forma = st.selectbox("Forma de Pagamento", opcoes_pgto, index=idx_pgto)
                        with col_f2:
                            edit_obs = st.text_area("Anotações / Obs", value=str(cur_os['Observacoes']) if pd.notna(cur_os['Observacoes']) else "", height=68)

                        st.write("")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            btn_salvar_os = st.form_submit_button("💾 SALVAR VALORES E DADOS", use_container_width=True)
                        with col_btn2:
                            btn_del_os = st.form_submit_button("🗑️ EXCLUIR ESTA OS", use_container_width=True)

                        if btn_salvar_os:
                            if not edit_servico.strip():
                                st.warning("A descrição do serviço não pode ficar vazia!")
                            else:
                                df_vendas.at[idx_os, "Servico"] = edit_servico.strip()
                                df_vendas.at[idx_os, "ValorTotal"] = edit_vtotal
                                df_vendas.at[idx_os, "ValorPago"] = edit_vpago
                                df_vendas.at[idx_os, "DataHoraEntrada"] = edit_ent.strip()
                                df_vendas.at[idx_os, "DataHoraSaida"] = edit_sai.strip()
                                df_vendas.at[idx_os, "FormaPagamento"] = edit_forma
                                df_vendas.at[idx_os, "Observacoes"] = edit_obs.strip()
                                
                                salvar_aba("Vendas", df_vendas)
                                st.success("Ordem de serviço salva no Google Sheets!")
                                st.rerun()

                        if btn_del_os:
                            df_vendas = df_vendas.drop(idx_os)
                            salvar_aba("Vendas", df_vendas)
                            st.success("Ordem de serviço removida do Google Sheets!")
                            st.rerun()
            else:
                st.info("Nenhum histórico financeiro de OS encontrado para este cliente.")

# ==========================================
# ABA 3: DESEMPENHO DO MÊS
# ==========================================
elif menu == "📈 Desempenho do Mês":
    st.subheader("📈 Controle e Desempenho Financeiro (Dados da Nuvem)")
    
    if not df_vendas.empty:
        df_completo_vendas = df_vendas.copy()
        if not df_clientes.empty:
            df_completo_vendas = df_vendas.merge(df_clientes[["ID", "Nome"]], left_on="ClienteID", right_on="ID", how="left", suffixes=('', '_cli'))
        
        total_faturado = df_completo_vendas["ValorTotal"].sum()
        total_recebido = df_completo_vendas["ValorPago"].sum()
        total_pendente = total_faturado - total_recebido
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("💰 Faturamento Total Bruto", f"R$ {total_faturado:,.2f}")
        with m2:
            st.metric("✅ Valor Efetivamente Pago", f"R$ {total_recebido:,.2f}", delta=f"{(total_recebido/total_faturado*100 if total_faturado > 0 else 0):.1f}% do Total")
        with m3:
            st.metric("⏳ Contas a Receber (Em Aberto)", f"R$ {total_pendente:,.2f}", delta="- Pendente" if total_pendente > 0 else "Sem pendências", delta_color="inverse")
            
        st.divider()
        
        col_graficos1, col_graficos2 = st.columns(2)
        
        with col_graficos1:
            st.markdown("#### 💳 Meios de Pagamento mais utilizados")
            meios_pgto = df_completo_vendas.groupby("FormaPagamento")["ValorTotal"].sum()
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor('#1e293b') 
            ax.set_facecolor('#1e293b')
            
            meios_pgto.plot(kind="bar", color="#06b6d4", ax=ax)
            ax.tick_params(colors="white")
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylabel("Total (R$)", color="white")
            ax.set_xlabel("", color="white")
            st.pyplot(fig)
            
        with col_graficos2:
            st.markdown("#### Últimas Ordens de Serviço Registradas")
            colunas_exibir = ["ID", "Nome", "Servico", "ValorTotal", "ValorPago", "DataCompra", "FormaPagamento"]
            colunas_existentes = [c for c in colunas_exibir if c in df_completo_vendas.columns]
            st.dataframe(df_completo_vendas[colunas_existentes].head(10), use_container_width=True, hide_index=True)
            
    else:
        st.info("Nenhuma ordem de serviço foi lançada ainda para computar o desempenho do mês.")
