import streamlit as st
import sqlite3
import os
import io
import calendar
import pandas as pd
import matplotlib.pyplot as plt
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

# BANCO DE DADOS
BANCO_DADOS = "JotaMotors_Completo.db"

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
    /* Estilização dos blocos e espaçamentos */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* Customização dos botões padrões do Streamlit */
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
    
    /* Botões vermelhos (como Excluir) */
    div.stButton > button[key*="excluir"] {
        background-color: #ef4444 !important;
    }
    div.stButton > button[key*="excluir"]:hover {
        background-color: #dc2626 !important;
    }

    /* Ajuste para inputs ficarem alinhados */
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
        KMEntrada TEXT, KMSaida TEXT, DataEntrada TEXT, DataSaida TEXT
    )""")

    # Criação da tabela de Vendas/OS incluindo as novas colunas
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

    # ---------------------------------------------------------
    # MIGRATION: Adicionar colunas novas se a tabela já existia
    # ---------------------------------------------------------
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

    # Usuários Padrão
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

# Tela de Login Centralizada e Compacta
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

# ==========================================
# CÓDIGO DO SISTEMA (APÓS LOGIN)
# ==========================================

# Barra Lateral de Navegação
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

# Cabeçalho Fixo do JotaMotors
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
                            st.rerun()
                            
                    if btn_excluir:
                        conexao = sqlite3.connect(BANCO_DADOS)
                        cursor = conexao.cursor()
                        cursor.execute("DELETE FROM Produtos WHERE ID=?", (selected_prod_id,))
                        conexao.commit()
                        conexao.close()
                        st.success("Produto removido!")
                        st.rerun()

# ==========================================
# ABA 2: GESTÃO DE CLIENTES
# ==========================================
elif menu == "👥 Gestão de Clientes":
    st.subheader("👥 Fichas de Clientes e Ordens de Serviços")
    
    conexao = sqlite3.connect(BANCO_DADOS)
    cursor = conexao.cursor()
    cursor.execute("SELECT ID, Nome, Telefone, ModeloMoto, AnoMoto, DataEntrada, DataSaida FROM Clientes")
    dados_clientes = cursor.fetchall()
    conexao.close()
    
    df_cli = pd.DataFrame(dados_clientes, columns=["ID", "Nome do Cliente", "Telefone", "Modelo Moto", "Ano Moto", "Data Entrada", "Data Saída"])
    
    busca_cli = st.text_input("🔎 Pesquisar Ficha de Clientes (Busque por Nome ou Modelo da Moto):", placeholder="Ex: Honda CG, João...")
    if busca_cli:
        df_cli = df_cli[
            df_cli['Nome do Cliente'].astype(str).str.contains(busca_cli, case=False) |
            df_cli['Modelo Moto'].astype(str).str.contains(busca_cli, case=False)
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
                    c_kme = st.text_input("KM de Entrada")
                    c_dent = st.text_input("Entrada (DD/MM/AAAA)")
                with col_m2:
                    c_ano = st.text_input("Ano da Moto")
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
                            INSERT INTO Clientes (Nome, Endereco, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida)
                            VALUES (?,?,?,?,?,?,?,?,?)
                        """, (c_nome.strip(), c_end.strip(), c_tel.strip(), c_mod.strip(), c_ano.strip(), c_kme.strip(), c_kms.strip(), c_dent.strip(), c_dsai.strip()))
                        conexao.commit()
                        conexao.close()
                        st.success("Ficha cadastrada com sucesso!")
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
                    
                    col_p_obs = st.columns([1, 1])
                    with col_p_obs:
                        os_forma_pagamento = st.selectbox(
                            "Forma de Pagamento", 
                            options=["Dinheiro", "Pix", "Cartão débito", "Cartão crédito"]
                        )
                    
                    os_obs_extra = st.text_area("Anotação / Observação Extra para o Cliente", placeholder="Escreva observações aqui...")

                    st.write("")
                    gravar_os = st.form_submit_button("LANÇAR ORDEM DE SERVIÇO", use_container_width=True)
                    if gravar_os:
                        if not os_desc.strip():
                            st.warning("A descrição da OS é obrigatória!")
                        else:
                            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                            # Conversão amigável de datas e horários da OS
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
                            st.rerun()

    with col_c2:
        st.markdown("### ✏️ Alterar ou Remover Cliente")
        with st.container(border=True):
            cli_dict_ed = {f"{c[1]} (ID: {c[0]})": c[0] for c in dados_clientes}
            sel_cli_ed = st.selectbox("Escolha o cliente para atualizar", [""] + list(cli_dict_ed.keys()))
            
            if sel_cli_ed:
                target_cli_id = cli_dict_ed[sel_cli_ed]
                conexao = sqlite3.connect(BANCO_DADOS)
                c_info = conexao.execute("SELECT Nome, Endereco, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida FROM Clientes WHERE ID=?", (target_cli_id,)).fetchone()
                conexao.close()
                
                with st.form("form_edit_cli"):
                    ec_nome = st.text_input("Nome Completo", value=c_info[0] or "")
                    ec_end = st.text_input("Endereço Completo", value=c_info[1] or "")
                    ec_tel = st.text_input("Telefone de Contato", value=c_info[2] or "")
                    
                    col_me1, col_me2 = st.columns(2)
                    with col_me1:
                        ec_mod = st.text_input("Modelo da Moto", value=c_info[3] or "")
                        ec_kme = st.text_input("KM Entrada", value=c_info[5] or "")
                        ec_dent = st.text_input("Data Entrada", value=c_info[7] or "")
                    with col_me2:
                        ec_ano = st.text_input("Ano Moto", value=c_info[4] or "")
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
                                UPDATE Clientes SET Nome=?, Endereco=?, Telefone=?, ModeloMoto=?, AnoMoto=?, KMEntrada=?, KMSaida=?, DataEntrada=?, DataSaida=?
                                WHERE ID=?
                            """, (ec_nome.strip(), ec_end.strip(), ec_tel.strip(), ec_mod.strip(), ec_ano.strip(), ec_kme.strip(), ec_kms.strip(), ec_dent.strip(), ec_dsai.strip(), target_cli_id))
                            conexao.commit()
                            conexao.close()
                            st.success("Ficha atualizada com sucesso!")
                            st.rerun()
                            
                    if submit_del_cli:
                        conexao = sqlite3.connect(BANCO_DADOS)
                        cursor = conexao.cursor()
                        cursor.execute("DELETE FROM Clientes WHERE ID=?", (target_cli_id,))
                        cursor.execute("DELETE FROM Vendas WHERE ClienteID=?", (target_cli_id,))
                        conexao.commit()
                        conexao.close()
                        st.success("Cliente removido permanentemente!")
                        st.rerun()

    # Histórico de Serviços / Gerador de Extrato
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
        
        # Meta informações
        cli_meta = cursor.execute("SELECT Nome, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida FROM Clientes WHERE ID=?", (cli_id_h,)).fetchone()
        conexao.close()
        
        with st.container(border=True):
            st.markdown(f"🏍️ **Moto registrada:** {cli_meta[2] or 'Não cadastrada'} (Ano: {cli_meta[3] or 'N/A'})")
            st.markdown(f"📍 **KM Entrada / Saída:** `{cli_meta[4] or '-'}` / `{cli_meta[5] or '-'}` | **Entrada/Saída Oficina:** {cli_meta[6] or '-'} a {cli_meta[7] or '-'}")
            
            if historico:
                df_hist = pd.DataFrame(historico, columns=[
                    "OS #", "Data Lançamento", "Serviços & Peças de Reposição", 
                    "Total Orçado (R$)", "Total Pago (R$)", "Entrada Oficial", "Saída Oficial", "Forma Pagamento", "Anotações / Obs"
                ])
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
                
                # Gerar PDF do Extrato com as Novas Funções Integradas
                def gerar_extrato_pdf_bytes(vendas_lista, c_meta):
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=letter)
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(50, 750, "EXTRATO DE SERVIÇOS - JOTAMOTORS")

                    c.setFont("Helvetica", 12)
                    c.drawString(50, 720, f"Cliente: {c_meta[0]}")
                    c.drawString(50, 700, f"Moto: {c_meta[2] or 'N/A'} (Ano: {c_meta[3] or 'N/A'}) | KM: {c_meta[4] or '-'} / {c_meta[5] or '-'}")
                    c.drawString(50, 680, f"Entrada/Saída: {c_meta[6] or '-'} / {c_meta[7] or '-'}")
                    c.line(50, 670, 550, 670)

                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(50, 650, "DETALHAMENTO DOS LANÇAMENTOS")
                    c.line(50, 645, 550, 645)

                    y = 625
                    total_extrato = 0.0

                    for d in vendas_lista:
                        if y < 130:
                            c.showPage()
                            y = 750
                        
                        c.setFont("Helvetica-Bold", 10)
                        c.drawString(50, y, f"OS #{d[0]} | Registrado em: {d[1]}")
                        y -= 15
                        
                        c.setFont("Helvetica", 10)
                        c.drawString(60, y, f"Entrada na Oficina: {d[5] if d[5] else 'N/A'} | Saída: {d[6] if d[6] else 'N/A'}")
                        y -= 15
                        c.drawString(60, y, f"Serviço/Peça: {d[2]}")
                        y -= 15
                        c.drawString(60, y, f"Forma de Pagamento: {d[7]} | Pago: R$ {d[4]:.2f} / Total Orçado: R$ {d[3]:.2f}")
                        y -= 15
                        
                        if d[8] and str(d[8]).strip() != "":
                            c.drawString(60, y, f"Anotação Cliente: {d[8]}")
                            y -= 15
                        
                        total_extrato += float(d[3] or 0.0)
                        c.setStrokeColor(HexColor("#cbd5e1"))
                        c.setLineWidth(0.5)
                        c.line(50, y, 550, y)
                        y -= 15

                    c.line(50, y+5, 550, y+5)
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(350, y-20, f"TOTAL DE SERVIÇOS: R$ {total_extrato:.2f}")

                    c.save()
                    buffer.seek(0)
                    return buffer.getvalue()
                    
                pdf_extrato = gerar_extrato_pdf_bytes(historico, cli_meta)
                st.download_button(
                    label="🖨️ Exportar Extrato Completo (PDF)",
                    data=pdf_extrato,
                    file_name=f"extrato_{cli_meta[0].replace(' ', '_').lower()}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("Este cliente não possui histórico de Ordens de Serviços cadastradas.")

# ==========================================
# ABA 3: DESEMPENHO FINANCEIRO DO MÊS
# ==========================================
elif menu == "📈 Desempenho do Mês":
    st.subheader("📊 Faturamento do Mês Consolidado")
    
    hoje = datetime.now()
    mes_atual_str = hoje.strftime("/%m/%Y")

    conexao = sqlite3.connect(BANCO_DADOS)
    cursor = conexao.cursor()
    cursor.execute("SELECT ValorPago, DataCompra FROM Vendas WHERE DataCompra LIKE ?", (f"%{mes_atual_str}%",))
    vendas = cursor.fetchall()
    conexao.close()

    num_dias = calendar.monthrange(hoje.year, hoje.month)[1]
    faturamento_diario = {d: 0.0 for d in range(1, num_dias + 1)}

    for valor, data_str in vendas:
        if valor is None or not data_str:
            continue
        try:
            dia = int(data_str.split()[0].split('/')[0])
            if dia in faturamento_diario:
                faturamento_diario[dia] += float(valor)
        except Exception:
            pass

    dias = list(faturamento_diario.keys())
    valores = list(faturamento_diario.values())
    total_mes = sum(valores)
    
    # Organização das métricas em colunas
    col_metrica1, col_metrica2 = st.columns(2)
    with col_metrica1:
        with st.container(border=True):
            st.metric("💰 Faturamento Total do Mês", f"R$ {total_mes:,.2f}")
            
    with col_metrica2:
        with st.container(border=True):
            media_diaria = total_mes / num_dias
            st.metric("📅 Média Diária Estimada", f"R$ {media_diaria:,.2f}")

    st.write("")
    st.markdown("### 📊 Histórico de Evolução Diária")
    
    # Configuração e renderização do gráfico usando Matplotlib alinhado ao tema escuro
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=COR_BG)
    ax.set_facecolor(COR_CARD)
    
    # Plotagem da linha de faturamento diário
    ax.plot(dias, valores, color=COR_ACCENT_CYAN, marker='o', markersize=4, linewidth=2, label="Faturamento")
    ax.fill_between(dias, valores, color=COR_ACCENT_CYAN, alpha=0.15)
    
    # Personalização dos eixos e textos
    ax.set_title(f"Faturamento Diário - {hoje.strftime('%m/%Y')}", color=COR_TEXT, fontsize=12, pad=15)
    ax.set_xlabel("Dia do Mês", color=COR_TEXT_MUTED, fontsize=10)
    ax.set_ylabel("Valor (R$)", color=COR_TEXT_MUTED, fontsize=10)
    
    # Ajustando cores das bordas e marcações para o tema dark
    ax.tick_params(colors=COR_TEXT_MUTED, labelsize=9)
    ax.spines['bottom'].set_color(COR_TEXT_MUTED)
    ax.spines['left'].set_color(COR_TEXT_MUTED)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Grade de fundo sutil
    ax.grid(True, linestyle=":", alpha=0.2, color=COR_TEXT_MUTED)
    
    # Exibe o gráfico de forma responsiva dentro do Streamlit
    st.pyplot(fig)
