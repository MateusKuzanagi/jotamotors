import streamlit as st
import sqlite3
import os
import io
import calendar
import pandas as pd
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Configuração da página do site
st.set_page_config(
    page_title="JotaMotors - Oficina Mecânica",
    page_icon="🏍️",
    layout="wide"
)

# BANCO DE DADOS E GOOGLE SHEETS
BANCO_DADOS = "JotaMotors_Completo.db"
ARQUIVO_CREDENCIAIS = "credenciais.json"  # Seu arquivo de chaves do Google Cloud
NOME_PLANILHA = "JotaMotors_AppSheet"       # Nome exato da sua Planilha no Drive

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
# FUNÇÃO DE SINCRONIZAÇÃO AUTOMÁTICA
# ==========================================
def sincronizar_com_appsheet():
    """Lê o SQLite local e atualiza as abas da planilha do Google Sheets."""
    try:
        escopos = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        credenciais = ServiceAccountCredentials.from_json_keyfile_name(ARQUIVO_CREDENCIAIS, escopos)
        cliente_gspread = gspread.authorize(credenciais)
        planilha = cliente_gspread.open(NOME_PLANILHA)
        
        conexao = sqlite3.connect(BANCO_DADOS)
        tabelas = ["Clientes", "Vendas", "Produtos"]
        
        for tabela in tabelas:
            df = pd.read_sql_query(f"SELECT * FROM {tabela}", conexao)
            df = df.fillna("").astype(str)
            
            try:
                aba = planilha.worksheet(tabela)
            except gspread.exceptions.WorksheetNotFound:
                aba = planilha.add_worksheet(title=tabela, rows="100", cols="20")
            
            aba.clear()
            cabecalho = df.columns.tolist()
            valores = df.values.tolist()
            aba.update("A1", [cabecalho] + valores)
            
        conexao.close()
        st.toast("⚡ AppSheet sincronizado com sucesso!", icon="🔄")
    except Exception as e:
        st.error(f"Erro na sincronização automática do AppSheet: {e}")

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
# INICIALIZAÇÃO DO BANCO DE DADOS
# ==========================================
def init_db():
    conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Usuarios(
        ID INTEGER PRIMARY KEY AUTOINCREMENT, Nome TEXT UNIQUE, Senha TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Clientes(
        ID INTEGER PRIMARY KEY AUTOINCREMENT, Nome TEXT, Endereco TEXT,
        Telefone TEXT, ModeloMoto TEXT, AnoMoto TEXT, KM TEXT,
        KMEntrada TEXT, KMSaida TEXT, DataEntrada TEXT, DataSaida TEXT,
        Placa TEXT DEFAULT ''
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Vendas(
        ID INTEGER PRIMARY KEY AUTOINCREMENT, 
        ClienteID INTEGER, 
        Servico TEXT,
        ValorTotal REAL, 
        ValorPago REAL, 
        DataCompra TEXT,
        DataHoraEntrada TEXT,
        DataHoraSaida TEXT,
        FormaPagamento TEXT,
        Observacoes TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produtos(
        ID TEXT PRIMARY KEY, NomeProduto TEXT, Descricao TEXT,
        Preco REAL, QtdEstoque INTEGER DEFAULT NULL
    )""")

    # Migrations
    cursor.execute("PRAGMA table_info(Clientes)")
    colunas_clientes = [col[1] for col in cursor.fetchall()]
    if "Placa" not in colunas_clientes:
        cursor.execute("ALTER TABLE Clientes ADD COLUMN Placa TEXT DEFAULT ''")

    cursor.execute("PRAGMA table_info(Vendas)")
    colunas_vendas = [col[1] for col in cursor.fetchall()]
    if "DataHoraEntrada" not in colunas_vendas:
        cursor.execute("ALTER TABLE Vendas ADD COLUMN DataHoraEntrada TEXT DEFAULT ''")
    if "DataHoraSaida" not in colunas_vendas:
        cursor.execute("ALTER TABLE Vendas ADD COLUMN DataHoraSaida TEXT DEFAULT ''")
    if "FormaPagamento" not in colunas_vendas:
        cursor.execute("ALTER TABLE Vendas ADD COLUMN FormaPagamento TEXT DEFAULT 'Dinheiro'")
    if "Observacoes" not in colunas_vendas:
        cursor.execute("ALTER TABLE Vendas ADD COLUMN Observacoes TEXT DEFAULT ''")

    usuarios_padrao = [('admin', '123'), ('maironxd', '14125'), ('luana', '14125'), ('josue', '123')]
    for user, senha in usuarios_padrao:
        cursor.execute("SELECT * FROM Usuarios WHERE Nome=?", (user,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Usuarios VALUES (NULL,?,?)", (user, senha))

    conexao.commit()
    conexao.close()

init_db()

# ==========================================
# CONTROLE DE SESSÃO (LOGIN)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ""

def verificar_login(u, p):
    conexao = sqlite3.connect(BANCO_DADOS)
    usuario = conexao.execute("SELECT * FROM Usuarios WHERE Nome=? AND Senha=?", (u.strip(), p.strip())).fetchone()
    conexao.close()
    return usuario

if not st.session_state['logged_in']:
    st.write("")
    st.write("")
    st.write("")
    col_lateral_esq, col_login_central, col_lateral_dir = st.columns([1, 1.2, 1])
    with col_login_central:
        st.markdown("<h1 style='text-align: center; color: #06b6d4; margin-bottom: 0px;'>🔑 JotaMotors ERP</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 20px;'>Painel de Gestão e Login Integrado</p>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form", clear_on_submit=False):
                user_input = st.text_input("Usuário")
                pass_input = st.text_input("Senha", type="password")
                st.write("")
                entrar = st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True)
                if entrar:
                    usuario_valido = verificar_login(user_input, pass_input)
                    if usuario_valido:
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = usuario_valido[1]
                        st.success("Acesso autorizado! Carregando...")
                        st.rerun()
                    else:
                        st.error("Usuário ou Senha incorretos!")
    st.stop()

# NAV BAR
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

col_logo, col_logo_dir = st.columns([2, 1])
with col_logo:
    st.markdown("<h1 style='color: #06b6d4; margin-bottom: 0px; padding-bottom:0px;'>JotaMotors</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 13px; margin-top:0px;'>SISTEMA DE GERENCIAMENTO DE OFICINA</p>", unsafe_allow_html=True)

st.divider()

# ==========================================
# ABA 1: DASHBOARD & ESTOQUE
# ==========================================
if menu == "📊 Dashboard & Estoque":
    conexao = sqlite3.connect(BANCO_DADOS)
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM Produtos")
    dados_produtos = cursor.fetchall()
    
    mes_atual = datetime.now().strftime("/%m/%Y")
    cursor.execute("SELECT ValorPago FROM Vendas WHERE DataCompra LIKE ?", (f"%{mes_atual}%",))
    vendas_mes = cursor.fetchall()
    lucro_mes = sum([v[0] for v in vendas_mes if v[0] is not None])
    conexao.close()
    
    total_produtos = len(dados_produtos)
    total_itens = 0
    valor_estoque = 0.0
    estoque_baixo = 0
    
    for d in dados_produtos:
        v_preco = d[3] if d[3] is not None else 0.0
        v_qtd = d[4]
        if v_qtd is not None and str(v_qtd).isdigit():
            total_itens += int(v_qtd)
            valor_estoque += float(v_preco) * int(v_qtd)
            if int(v_qtd) <= 3: 
                estoque_baixo += 1

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
    st.subheader("📦 Consulta de Estoque de Peças")
    df_prod = pd.DataFrame(dados_produtos, columns=["CÓDIGO/ID", "NOME DO PRODUTO", "DESCRIÇÃO", "PREÇO R$", "QTD ESTOQUE"])
    
    col_filtro, col_b1, col_b2 = st.columns([3, 1, 1])
    with col_filtro:
        busca_prod = st.text_input("🔎 Digite para pesquisar produto (Código ou Nome):", label_visibility="collapsed", placeholder="Buscar por código ou nome do produto...")
    
    if busca_prod:
        df_prod = df_prod[
            df_prod['CÓDIGO/ID'].astype(str).str.contains(busca_prod, case=False) | 
            df_prod['NOME DO PRODUTO'].astype(str).str.contains(busca_prod, case=False)
        ]
    
    st.dataframe(df_prod, use_container_width=True, hide_index=True)

    with col_b1:
        csv_data = df_prod.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(
            label="📊 Baixar Excel (CSV)",
            data=csv_data,
            file_name="estoque_jotamotors.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with col_b2:
        def exportar_produtos_pdf_bytes(dados):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 750, "RELATÓRIO DE ESTOQUE - JOTAMOTORS")
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, 720, "CÓDIGO")
            c.drawString(150, 720, "PRODUTO")
            c.drawString(350, 720, "PREÇO")
            c.drawString(450, 720, "ESTOQUE")
            c.line(50, 715, 550, 715)
            y = 700
            c.setFont("Helvetica", 10)
            for d in dados:
                if y < 50:
                    c.showPage()
                    y = 750
                c.drawString(50, y, str(d[0]))
                c.drawString(150, y, str(d[1])[:35])
                c.drawString(350, y, f"R$ {d[3]:.2f}")
                c.drawString(450, y, str(d[4] if d[4] is not None else "Aberto"))
                y -= 20
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
        
        pdf_estoque = exportar_produtos_pdf_bytes(dados_produtos)
        st.download_button(
            label="📕 Baixar PDF Estoque",
            data=pdf_estoque,
            file_name="estoque_jotamotors.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.divider()
    col_cad, col_ed = st.columns(2)

    with col_cad:
        st.markdown("### ➕ Novo Cadastro")
        with st.container(border=True):
            with st.form("form_add_prod", clear_on_submit=True):
                new_cod = st.text_input("Código/ID do Produto (Manual)*")
                new_nome = st.text_input("Nome do Produto*")
                new_desc = st.text_input("Descrição")
                new_preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=0.01)
                new_qtd = st.number_input("Quantidade Inicial em Estoque", min_value=0, step=1, value=0)
                salvar_novo = st.form_submit_button("CADASTRAR PRODUTO", use_container_width=True)
                if salvar_novo:
                    if not new_cod.strip() or not new_nome.strip():
                        st.warning("Código e Nome são obrigatórios!")
                    else:
                        try:
                            conexao = sqlite3.connect(BANCO_DADOS)
                            cursor = conexao.cursor()
                            cursor.execute("INSERT INTO Produtos (ID, NomeProduto, Descricao, Preco, QtdEstoque) VALUES (?, ?, ?, ?, ?)",
                                           (new_cod.strip(), new_nome.strip(), new_desc.strip(), new_preco, new_qtd))
                            conexao.commit()
                            conexao.close()
                            st.success("Produto adicionado com sucesso!")
                            sincronizar_com_appsheet() # AUTOMÁTICO
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Este Código/ID já existe no banco de dados!")

    with col_ed:
        st.markdown("### ✏️ Modificar Produto")
        with st.container(border=True):
            prod_ids = [p[0] for p in dados_produtos]
            selected_prod_id = st.selectbox("Escolha um produto para editar", [""] + prod_ids)
            if selected_prod_id:
                selected_prod = [p for p in dados_produtos if p[0] == selected_prod_id][0]
                with st.form("form_edit_prod"):
                    st.info(f"Editando Produto: {selected_prod[0]}")
                    edit_nome = st.text_input("Nome do Produto", value=selected_prod[1])
                    edit_desc = st.text_input("Descrição", value=selected_prod[2] or "")
                    edit_preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=0.01, value=float(selected_prod[3] or 0.0))
                    edit_qtd = st.number_input("Quantidade em Estoque", min_value=0, step=1, value=int(selected_prod[4]) if selected_prod[4] is not None else 0)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        btn_salvar = st.form_submit_button("💾 SALVAR", use_container_width=True)
                    with col_btn2:
                        btn_excluir = st.form_submit_button("🗑️ EXCLUIR", use_container_width=True)
                        
                    if btn_salvar:
                        if not edit_nome.strip():
                            st.warning("O nome não pode ser vazio!")
                        else:
                            conexao = sqlite3.connect(BANCO_DADOS)
                            cursor = conexao.cursor()
                            cursor.execute("UPDATE Produtos SET NomeProduto=?, Descricao=?, Preco=?, QtdEstoque=? WHERE ID=?",
                                           (edit_nome.strip(), edit_desc.strip(), edit_preco, edit_qtd, selected_prod_id))
                            conexao.commit()
                            conexao.close()
                            st.success("Alterações salvas!")
                            sincronizar_com_appsheet() # AUTOMÁTICO
                            st.rerun()
                            
                    if btn_excluir:
                        conexao = sqlite3.connect(BANCO_DADOS)
                        cursor = conexao.cursor()
                        cursor.execute("DELETE FROM Produtos WHERE ID=?", (selected_prod_id,))
                        conexao.commit()
                        conexao.close()
                        st.success("Produto removido!")
                        sincronizar_com_appsheet() # AUTOMÁTICO
                        st.rerun()

# ==========================================
# ABA 2: GESTÃO DE CLIENTES
# ==========================================
elif menu == "👥 Gestão de Clientes":
    st.subheader("👥 Fichas de Clientes e Ordens de Serviços")
    conexao = sqlite3.connect(BANCO_DADOS)
    cursor = conexao.cursor()
    cursor.execute("SELECT ID, Nome, Telefone, ModeloMoto, AnoMoto, DataEntrada, DataSaida, Placa FROM Clientes")
    dados_clientes = cursor.fetchall()
    conexao.close()
    
    df_cli = pd.DataFrame(dados_clientes, columns=["ID", "Nome do Cliente", "Telefone", "Modelo Moto", "Ano Moto", "Data Entrada", "Data Saída", "Placa"])
    busca_cli = st.text_input("🔎 Pesquisar Ficha de Clientes (Busque por Nome, Modelo ou Placa da Moto):", placeholder="Ex: Honda CG, João, ABC1D23...")
    if busca_cli:
        df_cli = df_cli[
            df_cli['Nome do Cliente'].astype(str).str.contains(busca_cli, case=False) |
            df_cli['Modelo Moto'].astype(str).str.contains(busca_cli, case=False) |
            df_cli['Placa'].astype(str).str.contains(busca_cli, case=False)
        ]
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

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
                        conexao = sqlite3.connect(BANCO_DADOS)
                        cursor = conexao.cursor()
                        cursor.execute("""
                            INSERT INTO Clientes (Nome, Endereco, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida, Placa)
                            VALUES (?,?,?,?,?,?,?,?,?,?)
                        """, (c_nome.strip(), c_end.strip(), c_tel.strip(), c_mod.strip(), c_ano.strip(), c_kme.strip(), c_kms.strip(), c_dent.strip(), c_dsai.strip(), c_pla.strip().upper()))
                        conexao.commit()
                        conexao.close()
                        st.success("Ficha cadastrada com sucesso!")
                        sincronizar_com_appsheet() # AUTOMÁTICO
                        st.rerun()

        st.markdown("### 🛠️ Registrar Ordem de Serviço (Venda)")
        with st.container(border=True):
            cli_dict = {f"{c[1]} (ID: {c[0]})": c[0] for c in dados_clientes}
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
                    
                    col_p_obs1, col_p_obs2 = st.columns([1, 1])
                    with col_p_obs1:
                        os_forma_pagamento = st.selectbox("Forma de Pagamento", options=["Dinheiro", "Pix", "Cartão débito", "Cartão crédito"])
                    with col_p_obs2:
                        st.write("")

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
                            
                            conexao = sqlite3.connect(BANCO_DADOS)
                            cursor = conexao.cursor()
                            cursor.execute("""
                                INSERT INTO Vendas (
                                    ClienteID, Servico, ValorTotal, ValorPago, DataCompra, 
                                    DataHoraEntrada, DataHoraSaida, FormaPagamento, Observacoes
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                target_cli_id, os_desc.strip(), os_total, os_pago, data_atual,
                                entrada_completa, saida_completa, os_forma_pagamento, os_obs_extra.strip()
                            ))
                            conexao.commit()
                            conexao.close()
                            st.success("Ordem de serviço registrada com sucesso!")
                            sincronizar_com_appsheet() # AUTOMÁTICO
                            st.rerun()

    with col_c2:
        st.markdown("### ✏️ Alterar ou Remover Cliente")
        with st.container(border=True):
            cli_dict_ed = {f"{c[1]} (ID: {c[0]})": c[0] for c in dados_clientes}
            sel_cli_ed = st.selectbox("Escolha o cliente para atualizar", [""] + list(cli_dict_ed.keys()))
            if sel_cli_ed:
                target_cli_id = cli_dict_ed[sel_cli_ed]
                conexao = sqlite3.connect(BANCO_DADOS)
                c_info = conexao.execute("SELECT Nome, Endereco, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida, Placa FROM Clientes WHERE ID=?", (target_cli_id,)).fetchone()
                conexao.close()
                
                with st.form("form_edit_cli"):
                    ec_nome = st.text_input("Nome Completo", value=c_info[0] or "")
                    ec_end = st.text_input("Endereço Completo", value=c_info[1] or "")
                    ec_tel = st.text_input("Telefone de Contato", value=c_info[2] or "")
                    
                    col_me1, col_me2 = st.columns(2)
                    with col_me1:
                        ec_mod = st.text_input("Modelo da Moto", value=c_info[3] or "")
                        ec_pla = st.text_input("Placa da Moto", value=c_info[9] or "")  
                        ec_kme = st.text_input("KM Entrada", value=c_info[5] or "")
                        ec_dent = st.text_input("Data Entrada", value=c_info[7] or "")
                    with col_me2:
                        ec_ano = st.text_input("Ano Moto", value=c_info[4] or "")
                        st.write("")  
                        ec_kms = st.text_input("KM Saída", value=c_info[6] or "")
                        ec_dsai = st.text_input("Data Saída", value=c_info[8] or "")
                    
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
                            conexao = sqlite3.connect(BANCO_DADOS)
                            cursor = conexao.cursor()
                            cursor.execute("""
                                UPDATE Clientes SET Nome=?, Endereco=?, Telefone=?, ModeloMoto=?, AnoMoto=?, KMEntrada=?, KMSaida=?, DataEntrada=?, DataSaida=?, Placa=?
                                WHERE ID=?
                            """, (ec_nome.strip(), ec_end.strip(), ec_tel.strip(), ec_mod.strip(), ec_ano.strip(), ec_kme.strip(), ec_kms.strip(), ec_dent.strip(), ec_dsai.strip(), ec_pla.strip().upper(), target_cli_id))
                            conexao.commit()
                            conexao.close()
                            st.success("Ficha atualizada com sucesso!")
                            sincronizar_com_appsheet() # AUTOMÁTICO
                            st.rerun()
                            
                    if submit_del_cli:
                        conexao = sqlite3.connect(BANCO_DADOS)
                        cursor = conexao.cursor()
                        cursor.execute("DELETE FROM Clientes WHERE ID=?", (target_cli_id,))
                        cursor.execute("DELETE FROM Vendas WHERE ClienteID=?", (target_cli_id,))
                        conexao.commit()
                        conexao.close()
                        st.success("Cliente removido permanentemente!")
                        sincronizar_com_appsheet() # AUTOMÁTICO
                        st.rerun()

    st.divider()
    st.subheader("📜 Extrato e Histórico de Prontuários")
    cli_dict_h = {f"{c[1]} (ID: {c[0]})": c[0] for c in dados_clientes}
    sel_cli_hist = st.selectbox("Selecione o Cliente para detalhar o extrato financeiro", [""] + list(cli_dict_h.keys()))
    
    if sel_cli_hist:
        cli_id_h = cli_dict_h[sel_cli_hist]
        conexao = sqlite3.connect(BANCO_DADOS)
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT ID, DataCompra, Servico, ValorTotal, ValorPago, DataHoraEntrada, DataHoraSaida, FormaPagamento, Observacoes 
            FROM Vendas WHERE ClienteID=? ORDER BY ID DESC
        """, (cli_id_h,))
        historico = cursor.fetchall()
        cli_meta = cursor.execute("SELECT Nome, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida, Placa FROM Clientes WHERE ID=?", (cli_id_h,)).fetchone()
        conexao.close()
        
        with st.container(border=True):
            st.markdown(f"🏍️ **Moto registrada:** {cli_meta[2] or 'Não cadastrada'} (Ano: {cli_meta[3] or 'N/A'}) | **Placa:** `{cli_meta[8] or 'N/A'}`")
            st.markdown(f"📍 **KM Entrada / Saída:** `{cli_meta[4] or '-'}` / `{cli_meta[5] or '-'}` | **Entrada/Saída Oficina:** {cli_meta[6] or '-'} a {cli_meta[7] or '-'}")
            
            if historico:
                df_hist = pd.DataFrame(historico, columns=["OS #", "Data Lançamento", "Serviços & Peças de Reposição", "Total Orçado (R$)", "Total Pago (R$)", "Entrada Oficial", "Saída Oficial", "Forma Pagamento", "Anotações / Obs"])
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
                
                st.markdown("### ✏️ Editar ou Excluir Lançamento (OS)")
                os_dict = {f"OS #{d[0]} - {d[2]}"[:50] + "...": d[0] for d in historico}
                sel_os_ed = st.selectbox("Selecione a Ordem de Serviço que deseja alterar ou excluir:", [""] + list(os_dict.keys()))
                
                if sel_os_ed:
                    os_id_target = os_dict[sel_os_ed]
                    cur_os = [d for d in historico if d[0] == os_id_target][0]
                    
                    with st.form("form_edit_os"):
                        st.info(f"Alterando OS #{os_id_target}")
                        edit_servico = st.text_input("Serviços & Peças de Reposição", value=cur_os[2])
                        col_v1, col_v2 = st.columns(2)
                        with col_v1:
                            edit_vtotal = st.number_input("Total Orçado (R$)", value=float(cur_os[3] or 0.0), step=0.01)
                        with col_v2:
                            edit_vpago = st.number_input("Total Pago (R$)", value=float(cur_os[4] or 0.0), step=0.01)

                        col_dt1, col_dt2 = st.columns(2)
                        with col_dt1:
                            edit_ent = st.text_input("Entrada Oficial", value=cur_os[5] or "")
                        with col_dt2:
                            edit_sai = st.text_input("Saída Oficial", value=cur_os[6] or "")

                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            opcoes_pgto = ["Dinheiro", "Pix", "Cartão débito", "Cartão crédito"]
                            idx_pgto = opcoes_pgto.index(cur_os[7]) if cur_os[7] in opcoes_pgto else 0
                            edit_forma = st.selectbox("Forma de Pagamento", opcoes_pgto, index=idx_pgto)
                        with col_f2:
                            edit_obs = st.text_area("Anotações / Obs", value=cur_os[8] or "", height=68)

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
                                conexao = sqlite3.connect(BANCO_DADOS)
                                cursor = conexao.cursor()
                                cursor.execute("""
                                    UPDATE Vendas
                                    SET Servico=?, ValorTotal=?, ValorPago=?, DataHoraEntrada=?, DataHoraSaida=?, FormaPagamento=?, Observacoes=?
                                    WHERE ID=?
                                """, (edit_servico.strip(), edit_vtotal, edit_vpago, edit_ent.strip(), edit_sai.strip(), edit_forma, edit_obs.strip(), os_id_target))
                                conexao.commit()
                                conexao.close()
                                st.success("Ordem de Serviço atualizada com sucesso!")
                                sincronizar_com_appsheet() # AUTOMÁTICO
                                st.rerun()

                        if btn_del_os:
                            conexao = sqlite3.connect(BANCO_DADOS)
                            cursor = conexao.cursor()
                            cursor.execute("DELETE FROM Vendas WHERE ID=?", (os_id_target,))
                            conexao.commit()
                            conexao.close()
                            st.success("Ordem de Serviço excluída!")
                            sincronizar_com_appsheet() # AUTOMÁTICO
                            st.rerun()
            else:
                st.info("Este cliente ainda não possui ordens de serviços lançadas.")

# ==========================================
# ABA 3: DESEMPENHO DO MÊS
# ==========================================
elif menu == "📈 Desempenho do Mês":
    st.subheader("📈 Desempenho Financeiro & Métricas Mensais")
    conexao = sqlite3.connect(BANCO_DADOS)
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT V.ID, C.Nome, V.Servico, V.ValorTotal, V.ValorPago, V.DataCompra, V.FormaPagamento 
        FROM Vendas V 
        LEFT JOIN Clientes C ON V.ClienteID = C.ID
    """)
    todas_vendas = cursor.fetchall()
    conexao.close()
    
    if todas_vendas:
        df_vendas = pd.DataFrame(todas_vendas, columns=["ID", "Cliente", "Serviço", "Valor Total", "Valor Pago", "Data", "Pagamento"])
        mes_atual_nome = datetime.now().strftime("/%m/%Y")
        df_vendas['NoMes'] = df_vendas['Data'].apply(lambda x: mes_atual_nome in str(x))
        df_mes = df_vendas[df_vendas['NoMes'] == True].copy()
        
        if not df_mes.empty:
            total_orcado = df_mes['Valor Total'].sum()
            total_pago = df_mes['Valor Pago'].sum()
            restante_receber = total_orcado - total_pago
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                with st.container(border=True):
                    st.metric("📊 Total de OS (Mês)", f"{len(df_mes)} ordens")
            with m2:
                with st.container(border=True):
                    st.metric("💰 Total Faturado", f"R$ {total_orcado:,.2f}")
            with m3:
                with st.container(border=True):
                    st.metric("🟢 Valor Recebido", f"R$ {total_pago:,.2f}")
            with m4:
                with st.container(border=True):
                    st.metric("🔴 A Receber (Pendentes)", f"R$ {restante_receber:,.2f}")
                    
            st.divider()
            col_g1, col_g2 = st.columns([1.5, 1])
            with col_g1:
                st.write("📊 **Faturamento Mensal por Forma de Pagamento**")
                df_pagamentos = df_mes.groupby('Pagamento')['Valor Pago'].sum().reset_index()
                fig, ax = plt.subplots(figsize=(6, 3))
                fig.patch.set_facecolor('#1e293b')
                ax.set_facecolor('#1e293b')
                cores = ['#06b6d4', '#3b82f6', '#10b981', '#ef4444']
                ax.bar(df_pagamentos['Pagamento'], df_pagamentos['Valor Pago'], color=cores[:len(df_pagamentos)])
                ax.tick_params(colors='#f8fafc', labelsize=8)
                ax.spines['bottom'].set_color('#94a3b8')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#94a3b8')
                ax.set_ylabel("Valor (R$)", color='#f8fafc', fontsize=8)
                st.pyplot(fig)
                
            with col_g2:
                st.write("📋 **Lista das Últimas Vendas do Mês**")
                st.dataframe(df_mes[["Cliente", "Valor Total", "Valor Pago", "Pagamento"]].tail(5), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma venda ou OS registrada no mês corrente até o momento.")
    else:
        st.info("Ainda não existem vendas ou faturamentos registrados no banco de dados.")
