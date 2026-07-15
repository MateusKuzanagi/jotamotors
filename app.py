import streamlit as st
import sqlite3
import os
import io
import calendar
import hashlib  # Security: Criptografia de senhas
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
    div.stButton > button[key*="excluir"], div.stButton > button[key*="deletar"], div.stButton > button[key*="del_"] {
        background-color: #ef4444 !important;
    }
    div.stButton > button[key*="excluir"]:hover, div.stButton > button[key*="deletar"]:hover, div.stButton > button[key*="del_"]:hover {
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
# FUNÇÕES DE SEGURANÇA (CRIPTOGRAFIA)
# ==========================================
def codificar_senha(senha):
    """Cria um hash SHA-256 seguro da senha para que ela não fique em texto limpo."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

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
        PlacaMoto TEXT
    )""")

    # Atualização dinâmica de colunas na tabela Clientes
    try:
        cursor.execute("ALTER TABLE Clientes ADD COLUMN PlacaMoto TEXT")
    except sqlite3.OperationalError:
        pass 

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Vendas(
        ID INTEGER PRIMARY KEY AUTOINCREMENT, ClienteID INTEGER, Servico TEXT,
        ValorTotal REAL, ValorPago REAL, DataCompra TEXT, ProdutoID TEXT, QtdVendida INTEGER DEFAULT 0
    )""")

    # Atualização dinâmica de colunas na tabela Vendas (Baixa de estoque integrada)
    try:
        cursor.execute("ALTER TABLE Vendas ADD COLUMN ProdutoID TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE Vendas ADD COLUMN QtdVendida INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produtos(
        ID TEXT PRIMARY KEY, NomeProduto TEXT, Descricao TEXT,
        Preco REAL, QtdEstoque INTEGER DEFAULT NULL
    )""")

    # Usuários Padrão (Salvando com Hash Seguro!)
    usuarios_padrao = [('admin', '123'), ('maironxd', '14125'), ('luana', '14125'), ('josue', '123')]
    for user, senha in usuarios_padrao:
        cursor.execute("SELECT * FROM Usuarios WHERE Nome=?", (user,))
        if not cursor.fetchone():
            senha_segura = codificar_senha(senha)
            cursor.execute("INSERT INTO Usuarios VALUES (NULL,?,?)", (user, senha_segura))

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
    conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
    senha_criptografada = codificar_senha(p)
    usuario = conexao.execute("SELECT * FROM Usuarios WHERE Nome=? AND Senha=?", (u.strip(), senha_criptografada)).fetchone()
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
    
    conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
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
                            conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
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
                            conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
                            cursor = conexao.cursor()
                            cursor.execute("UPDATE Produtos SET NomeProduto=?, Descricao=?, Preco=?, QtdEstoque=? WHERE ID=?",
                                           (edit_nome.strip(), edit_desc.strip(), edit_preco, edit_qtd, selected_prod_id))
                            conexao.commit()
                            conexao.close()
                            st.success("Alterações salvas!")
                            st.rerun()
                            
                    if btn_excluir:
                        conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
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
    
    conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
    cursor = conexao.cursor()
    cursor.execute("SELECT ID, Nome, Telefone, ModeloMoto, AnoMoto, PlacaMoto, DataEntrada, DataSaida FROM Clientes")
    dados_clientes = cursor.fetchall()
    
    # Buscar lista de produtos para o menu de baixa de estoque
    cursor.execute("SELECT ID, NomeProduto, Preco, QtdEstoque FROM Produtos")
    lista_produtos_os = cursor.fetchall()
    conexao.close()
    
    df_cli = pd.DataFrame(dados_clientes, columns=["ID", "Nome do Cliente", "Telefone", "Modelo Moto", "Ano Moto", "Placa", "Data Entrada", "Data Saída"])
    
    busca_cli = st.text_input("🔎 Pesquisar Ficha de Clientes (Busque por Nome, Modelo da Moto ou Placa):", placeholder="Ex: Honda CG, João, ABC1D23...")
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
                    c_placa = st.text_input("Placa da Moto")
                    c_kme = st.text_input("KM de Entrada")
                with col_m2:
                    c_ano = st.text_input("Ano da Moto")
                    c_kms = st.text_input("KM de Saída")
                
                col_datas = st.columns(2)
                with col_datas[0]:
                    c_dent = st.text_input("Entrada (DD/MM/AAAA)")
                with col_datas[1]:
                    c_dsai = st.text_input("Saída (DD/MM/AAAA)")
                
                st.write("")
                gravar_cli = st.form_submit_button("GRAVAR FICHA DO CLIENTE", use_container_width=True)
                if gravar_cli:
                    if not c_nome.strip():
                        st.warning("Nome do cliente é obrigatório!")
                    else:
                        conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
                        cursor = conexao.cursor()
                        cursor.execute("""
                            INSERT INTO Clientes (Nome, Endereco, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida, PlacaMoto)
                            VALUES (?,?,?,?,?,?,?,?,?,?)
                        """, (c_nome.strip(), c_end.strip(), c_tel.strip(), c_mod.strip(), c_ano.strip(), c_kme.strip(), c_kms.strip(), c_dent.strip(), c_dsai.strip(), c_placa.strip().upper()))
                        conexao.commit()
                        conexao.close()
                        st.success("Ficha cadastrada com sucesso!")
                        st.rerun()

        # =========================================================
        # REGISTRO DE OS COM BAIXA AUTOMÁTICA DE ESTOQUE
        # =========================================================
        st.markdown("### 🛠️ Registrar Ordem de Serviço (Venda)")
        with st.container(border=True):
            cli_dict = {f"{c[1]} (ID: {c[0]})": c[0] for c in dados_clientes}
            sel_cli_venda = st.selectbox("Escolha o Cliente para associar a OS", [""] + list(cli_dict.keys()))
            
            if sel_cli_venda:
                target_cli_id = cli_dict[sel_cli_venda]
                with st.form("form_lancar_os", clear_on_submit=True):
                    
                    st.markdown("**Peças & Estoque (Baixa Automática)**")
                    prod_dict_os = {f"{p[1]} (Cód: {p[0]}) | Est: {p[3]} un | R$ {p[2]:.2f}": p for p in lista_produtos_os}
                    sel_prod_os = st.selectbox("Vincular Peça do Estoque (Opcional)", ["Nenhum (Apenas Serviço)"] + list(prod_dict_os.keys()))
                    
                    qtd_usada = 1
                    if sel_prod_os != "Nenhum (Apenas Serviço)":
                        prod_selecionado = prod_dict_os[sel_prod_os]
                        qtd_max = int(prod_selecionado[3]) if prod_selecionado[3] is not None else 999
                        qtd_usada = st.number_input("Quantidade Utilizada", min_value=1, max_value=max(1, qtd_max), value=1, step=1)
                        st.caption(f"Preço Unitário: **R$ {prod_selecionado[2]:.2f}** | Total Peça: **R$ {prod_selecionado[2] * qtd_usada:.2f}**")
                    
                    st.divider()
                    st.markdown("**Informações do Serviço**")
                    os_desc = st.text_input("Serviços Realizados / Mão de Obra*")
                    
                    col_os1, col_os2 = st.columns(2)
                    with col_os1:
                        os_total = st.number_input("Valor Total Orçamento (R$)", min_value=0.0, step=0.01)
                    with col_os2:
                        os_pago = st.number_input("Valor Pago de Adiantamento (R$)", min_value=0.0, step=0.01)
                    
                    st.write("")
                    gravar_os = st.form_submit_button("LANÇAR ORDEM DE SERVIÇO", use_container_width=True)
                    if gravar_os:
                        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                        conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
                        cursor = conexao.cursor()
                        
                        p_id = None
                        qtd_venda = 0
                        desc_final = os_desc.strip()
                        
                        # Se houver produto vinculado, dar baixa e anexar no texto
                        if sel_prod_os != "Nenhum (Apenas Serviço)":
                            prod_selecionado = prod_dict_os[sel_prod_os]
                            p_id = prod_selecionado[0]
                            p_nome = prod_selecionado[1]
                            qtd_venda = qtd_usada
                            
                            if not desc_final:
                                desc_final = f"{p_nome} (x{qtd_venda})"
                            else:
                                desc_final = f"{p_nome} (x{qtd_venda}) + {desc_final}"
                                
                            # Decrementar o estoque na tabela Produtos
                            cursor.execute("UPDATE Produtos SET QtdEstoque = QtdEstoque - ? WHERE ID = ?", (qtd_venda, p_id))
                        
                        if not desc_final:
                            st.warning("É necessário informar uma peça ou descrição de serviço!")
                        else:
                            cursor.execute("""
                                INSERT INTO Vendas (ClienteID, Servico, ValorTotal, ValorPago, DataCompra, ProdutoID, QtdVendida) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (target_cli_id, desc_final, os_total, os_pago, data_atual, p_id, qtd_venda))
                            
                            conexao.commit()
                            conexao.close()
                            st.success("Ordem de serviço registrada com baixa efetuada no estoque!")
                            st.rerun()

    with col_c2:
        st.markdown("### ✏️ Alterar ou Remover Cliente")
        with st.container(border=True):
            cli_dict_ed = {f"{c[1]} (ID: {c[0]})": c[0] for c in dados_clientes}
            sel_cli_ed = st.selectbox("Escolha o cliente para atualizar", [""] + list(cli_dict_ed.keys()))
            
            if sel_cli_ed:
                target_cli_id = cli_dict_ed[sel_cli_ed]
                conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
                c_info = conexao.execute("SELECT Nome, Endereco, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida, PlacaMoto FROM Clientes WHERE ID=?", (target_cli_id,)).fetchone()
                conexao.close()
                
                with st.form("form_edit_cli"):
                    ec_nome = st.text_input("Nome Completo", value=c_info[0] or "")
                    ec_end = st.text_input("Endereço Completo", value=c_info[1] or "")
                    ec_tel = st.text_input("Telefone de Contato", value=c_info[2] or "")
                    
                    col_me1, col_me2 = st.columns(2)
                    with col_me1:
                        ec_mod = st.text_input("Modelo da Moto", value=c_info[3] or "")
                        ec_placa = st.text_input("Placa da Moto", value=c_info[9] or "")
                        ec_kme = st.text_input("KM Entrada", value=c_info[5] or "")
                    with col_me2:
                        ec_ano = st.text_input("Ano Moto", value=c_info[4] or "")
                        ec_kms = st.text_input("KM Saída", value=c_info[6] or "")
                    
                    col_edatas = st.columns(2)
                    with col_edatas[0]:
                        ec_dent = st.text_input("Data Entrada", value=c_info[7] or "")
                    with col_edatas[1]:
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
                            conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
                            cursor = conexao.cursor()
                            cursor.execute("""
                                UPDATE Clientes SET Nome=?, Endereco=?, Telefone=?, ModeloMoto=?, AnoMoto=?, KMEntrada=?, KMSaida=?, DataEntrada=?, DataSaida=?, PlacaMoto=?
                                WHERE ID=?
                            """, (ec_nome.strip(), ec_end.strip(), ec_tel.strip(), ec_mod.strip(), ec_ano.strip(), ec_kme.strip(), ec_kms.strip(), ec_dent.strip(), ec_dsai.strip(), ec_placa.strip().upper(), target_cli_id))
                            conexao.commit()
                            conexao.close()
                            st.success("Ficha atualizada com sucesso!")
                            st.rerun()
                            
                    if submit_del_cli:
                        conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
                        cursor = conexao.cursor()
                        # Devolver o estoque de todas as OSs vinculadas antes de excluir o cliente
                        vendas_vinculadas = cursor.execute("SELECT ID, ProdutoID, QtdVendida FROM Vendas WHERE ClienteID=?", (target_cli_id,)).fetchall()
                        for v in vendas_vinculadas:
                            if v[1] and (v[2] or 0) > 0:
                                cursor.execute("UPDATE Produtos SET QtdEstoque = QtdEstoque + ? WHERE ID=?", (v[2], v[1]))
                        
                        cursor.execute("DELETE FROM Clientes WHERE ID=?", (target_cli_id,))
                        cursor.execute("DELETE FROM Vendas WHERE ClienteID=?", (target_cli_id,))
                        conexao.commit()
                        conexao.close()
                        st.success("Cliente e histórico removidos permanentemente!")
                        st.rerun()

    # Histórico de Serviços / Gerador de Extrato
    st.divider()
    st.subheader("📜 Extrato e Histórico de Prontuários")
    
    cli_dict_h = {f"{c[1]} (ID: {c[0]})": c[0] for c in dados_clientes}
    sel_cli_hist = st.selectbox("Selecione o Cliente para detalhar o extrato financeiro", [""] + list(cli_dict_h.keys()))
    
    if sel_cli_hist:
        cli_id_h = cli_dict_h[sel_cli_hist]
        conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
        cursor = conexao.cursor()
        cursor.execute("SELECT ID, DataCompra, Servico, ValorTotal, ValorPago FROM Vendas WHERE ClienteID=? ORDER BY ID DESC", (cli_id_h,))
        historico = cursor.fetchall()
        
        cli_meta = cursor.execute("SELECT Nome, Telefone, ModeloMoto, AnoMoto, KMEntrada, KMSaida, DataEntrada, DataSaida, PlacaMoto FROM Clientes WHERE ID=?", (cli_id_h,)).fetchone()
        conexao.close()
        
        with st.container(border=True):
            st.markdown(f"🏍️ **Moto registrada:** {cli_meta[2] or 'Não cadastrada'} (Ano: {cli_meta[3] or 'N/A'}) | **Placa:** `{cli_meta[8] or 'N/A'}`")
            st.markdown(f"📍 **KM Entrada / Saída:** `{cli_meta[4] or '-'}` / `{cli_meta[5] or '-'}` | **Entrada/Saída Oficina:** {cli_meta[6] or '-'} a {cli_meta[7] or '-'}")
            
            if historico:
                # Tabela de Histórico Principal
                df_hist = pd.DataFrame(historico, columns=["OS #", "Data da OS", "Serviços & Peças de Reposição", "Total Orçado (R$)", "Total Pago (R$)"])
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
                
                # =========================================================
                # EDIÇÃO DIRETA DE VALORES (FINALIZADA E CORRIGIDA)
                # =========================================================
                st.write("")
                st.markdown("### ✏️ Editar Valores / Registrar Pagamentos")
                st.caption("Abra as abas abaixo para editar o serviço, alterar o valor total ou registrar o valor pago pelo cliente.")
                
                for os_item in historico:
                    os_id = os_item[0]
                    os_data = os_item[1]
                    os_desc = os_item[2]
                    os_total = float(os_item[3] or 0.0)
                    os_pago = float(os_item[4] or 0.0)
                    os_pendente = os_total - os_pago
                    
                    # Definindo se está quitada ou pendente
                    if os_pendente > 0:
                        status_label = f"🔴 Em Aberto (Falta pagar: R$ {os_pendente:.2f})"
                    else:
                        status_label = "🟢 Pago / Quitado"
                        
                    # Criando containers sanfonas únicos para cada OS
                    with st.expander(f"⚙️ OS #{os_id} - {os_desc[:40]}... | {status_label}"):
                        with st.form(f"form_edit_os_direct_{os_id}"):
                            eo_servico = st.text_input("Serviços Realizados / Peças", value=os_desc, key=f"desc_{os_id}")
                            
                            col_eo1, col_eo2 = st.columns(2)
                            with col_eo1:
                                eo_total = st.number_input("Valor Total Orçado (R$)", min_value=0.0, step=0.01, value=os_total, key=f"tot_{os_id}")
                            with col_eo2:
                                # CORREÇÃO DA LINHA CORTADA DO INPUT DO USUÁRIO
                                eo_pago = st.number_input("Valor Pago pelo Cliente (R$)", min_value=0.0, step=0.01, value=os_pago, key=f"pago_{os_id}")
                            
                            col_os_btn1, col_os_btn2 = st.columns(2)
                            with col_os_btn1:
                                os_salvar = st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True)
                            with col_os_btn2:
                                os_excluir = st.form_submit_button("🗑️ EXCLUIR ESTA OS", use_container_width=True)
                            
                            if os_salvar:
                                conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
                                cursor = conexao.cursor()
                                cursor.execute("UPDATE Vendas SET Servico=?, ValorTotal=?, ValorPago=? WHERE ID=?", 
                                               (eo_servico.strip(), eo_total, eo_pago, os_id))
                                conexao.commit()
                                conexao.close()
                                st.success(f"OS #{os_id} atualizada com sucesso!")
                                st.rerun()
                                
                            if os_excluir:
                                conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
                                cursor = conexao.cursor()
                                # Devolver o item ao estoque ao deletar a OS
                                os_info = cursor.execute("SELECT ProdutoID, QtdVendida FROM Vendas WHERE ID=?", (os_id,)).fetchone()
                                if os_info and os_info[0] and (os_info[1] or 0) > 0:
                                    cursor.execute("UPDATE Produtos SET QtdEstoque = QtdEstoque + ? WHERE ID=?", (os_info[1], os_info[0]))
                                
                                cursor.execute("DELETE FROM Vendas WHERE ID=?", (os_id,))
                                conexao.commit()
                                conexao.close()
                                st.success(f"OS #{os_id} removida com sucesso!")
                                st.rerun()

                # =========================================================
                # NOVO: EXPORTADOR DE EXTRATO/ORÇAMENTO EM PDF DO CLIENTE
                # =========================================================
                st.write("")
                st.markdown("### 🖨️ Imprimir Prontuário / PDF")
                
                def exportar_cliente_pdf_bytes(cli_meta, historico):
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=letter)
                    
                    # Cabeçalho do PDF
                    c.setFillColor(HexColor("#020617"))
                    c.setFont("Helvetica-Bold", 18)
                    c.drawString(50, 750, "JotaMotors - Ficha Financeira de Prontuário")
                    
                    c.setFont("Helvetica", 10)
                    c.setFillColor(HexColor("#475569"))
                    c.drawString(50, 732, f"Data do Relatório: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                    c.line(50, 722, 560, 722)
                    
                    # Bloco de Informações do Cliente
                    c.setFillColor(HexColor("#0f172a"))
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, 702, f"Cliente: {cli_meta[0]}")
                    c.setFont("Helvetica", 10)
                    c.drawString(50, 682, f"Telefone: {cli_meta[1] or 'Não Informado'}")
                    c.drawString(50, 667, f"Moto: {cli_meta[2] or 'Não Informada'} (Ano: {cli_meta[3] or 'N/A'}) | Placa: {cli_meta[8] or 'N/A'}")
                    c.drawString(50, 652, f"KM Entrada/Saída: {cli_meta[4] or '-'} / {cli_meta[5] or '-'}")
                    c.drawString(50, 637, f"Período na Oficina: {cli_meta[6] or '-'} até {cli_meta[7] or '-'}")
                    c.line(50, 622, 560, 622)
                    
                    # Títulos da Tabela de Serviços
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(50, 602, "OS #")
                    c.drawString(100, 602, "Data")
                    c.drawString(180, 602, "Serviços & Peças de Reposição")
                    c.drawString(400, 602, "Total (R$)")
                    c.drawString(480, 602, "Pago (R$)")
                    c.line(50, 592, 560, 592)
                    
                    y = 572
                    total_orcado = 0.0
                    total_pago = 0.0
                    c.setFont("Helvetica", 9)
                    c.setFillColor(HexColor("#1e293b"))
                    
                    for os_item in historico:
                        if y < 80:
                            c.showPage()
                            y = 750
                            c.setFont("Helvetica-Bold", 10)
                            c.drawString(50, 770, "OS #")
                            c.drawString(100, 770, "Data")
                            c.drawString(180, 770, "Serviços & Peças de Reposição")
                            c.drawString(400, 770, "Total (R$)")
                            c.drawString(480, 770, "Pago (R$)")
                            c.line(50, 760, 560, 760)
                            c.setFont("Helvetica", 9)
                            
                        c.drawString(50, y, f"#{os_item[0]}")
                        c.drawString(100, y, str(os_item[1])[:10])
                        c.drawString(180, y, str(os_item[2])[:38])
                        c.drawString(400, y, f"{os_item[3]:.2f}")
                        c.drawString(480, y, f"{os_item[4]:.2f}")
                        
                        total_orcado += float(os_item[3] or 0.0)
                        total_pago += float(os_item[4] or 0.0)
                        y -= 20
                        
                    c.line(50, y + 10, 560, y + 10)
                    y -= 10
                    
                    # Totalizadores finais
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(240, y, "TOTAIS ACUMULADOS:")
                    c.drawString(400, y, f"R$ {total_orcado:.2f}")
                    c.drawString(480, y, f"R$ {total_pago:.2f}")
                    
                    y -= 20
                    saldo_devedor = total_orcado - total_pago
                    if saldo_devedor > 0:
                        c.setFillColor(HexColor("#ef4444")) # Vermelho para débito
                        c.drawString(240, y, f"SALDO EM ABERTO: R$ {saldo_devedor:.2f}")
                    else:
                        c.setFillColor(HexColor("#10b981")) # Verde para quitado
                        c.drawString(240, y, "STATUS FINANCEIRO: QUITADO")
                    
                    c.save()
                    buffer.seek(0)
                    return buffer.getvalue()
                
                pdf_cliente = exportar_cliente_pdf_bytes(cli_meta, historico)
                st.download_button(
                    label="📄 Gerar Extrato / Fatura PDF",
                    data=pdf_cliente,
                    file_name=f"extrato_{cli_meta[0].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.info("Nenhum registro de serviço ou venda associado a este cliente.")

# ==========================================
# ABA 3: DESEMPENHO DO MÊS (DESENVOLVIDO POR COMPLETO)
# ==========================================
elif menu == "📈 Desempenho do Mês":
    st.subheader("📈 Relatório Mensal de Caixa e Faturamento")
    
    conexao = sqlite3.connect(BANCO_DADOS, timeout=30)
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT V.ID, V.DataCompra, V.Servico, V.ValorTotal, V.ValorPago, C.Nome 
        FROM Vendas V
        LEFT JOIN Clientes C ON V.ClienteID = C.ID
        ORDER BY V.ID DESC
    """)
    historico_vendas_geral = cursor.fetchall()
    conexao.close()
    
    if historico_vendas_geral:
        df_vendas = pd.DataFrame(historico_vendas_geral, columns=["ID OS", "Data", "Serviço/Peça", "Valor Total (R$)", "Valor Pago (R$)", "Cliente"])
        df_vendas["Valor Total (R$)"] = df_vendas["Valor Total (R$)"].fillna(0.0)
        df_vendas["Valor Pago (R$)"] = df_vendas["Valor Pago (R$)"].fillna(0.0)
        df_vendas["Pendente (R$)"] = df_vendas["Valor Total (R$)"] - df_vendas["Valor Pago (R$)"]
        
        # Estatísticas principais
        tot_geral_faturado = df_vendas["Valor Total (R$)"].sum()
        tot_geral_recebido = df_vendas["Valor Pago (R$)"].sum()
        tot_geral_pendente = df_vendas["Pendente (R$)"].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            with st.container(border=True):
                st.metric("📊 Faturamento Bruto (Orçado)", f"R$ {tot_geral_faturado:,.2f}")
        with col_m2:
            with st.container(border=True):
                st.metric("🟢 Valor Efetivamente Recebido", f"R$ {tot_geral_recebido:,.2f}", 
                          delta=f"{tot_geral_recebido/tot_geral_faturado*100:.1f}% do total" if tot_geral_faturado > 0 else "0.0%")
        with col_m3:
            with st.container(border=True):
                st.metric("🔴 Contas a Receber (Pendente)", f"R$ {tot_geral_pendente:,.2f}", 
                          delta="- Crítico" if tot_geral_pendente > 0 else "OK", delta_color="inverse")
                
        st.write("")
        st.markdown("### 📊 Gráficos de Controle Financeiro")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            with st.container(border=True):
                st.markdown("**Comparativo de Fluxo de Caixa**")
                
                # Gráfico estilizado com o tema escuro do JotaMotors
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0f172a') # COR_BG
                ax.set_facecolor('#1e293b') # COR_CARD
                
                categorias = ['Faturamento Bruto', 'Total Recebido', 'Total Pendente']
                valores = [tot_geral_faturado, tot_geral_recebido, tot_geral_pendente]
                cores = ['#3b82f6', '#10b981', '#ef4444'] # Azul, Verde, Vermelho
                
                barras = ax.bar(categorias, valores, color=cores, width=0.5)
                ax.tick_params(colors='#f8fafc', labelsize=10)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#334155')
                ax.spines['bottom'].set_color('#334155')
                ax.yaxis.grid(True, linestyle='--', alpha=0.3, color='#94a3b8')
                ax.set_axisbelow(True)
                
                for bar in barras:
                    height = bar.get_height()
                    ax.annotate(f'R$ {height:,.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', color='#f8fafc', fontsize=9)
                                
                st.pyplot(fig)
                
        with col_g2:
            with st.container(border=True):
                st.markdown("**Clientes que Mais Geraram Receita (Top 5)**")
                
                # Agrupamento para ranking de clientes
                df_ranking = df_vendas.groupby("Cliente")["Valor Total (R$)"].sum().reset_index()
                df_ranking = df_ranking.sort_values(by="Valor Total (R$)", ascending=False).head(5)
                
                if not df_ranking.empty:
                    fig2, ax2 = plt.subplots(figsize=(6, 4))
                    fig2.patch.set_facecolor('#0f172a')
                    ax2.set_facecolor('#1e293b')
                    
                    y_pos = range(len(df_ranking))
                    barras2 = ax2.barh(y_pos, df_ranking["Valor Total (R$)"], color='#06b6d4', height=0.5) # COR_ACCENT_CYAN
                    ax2.set_yticks(y_pos)
                    ax2.set_yticklabels(df_ranking["Cliente"], color='#f8fafc', fontsize=10)
                    ax2.tick_params(colors='#f8fafc', labelsize=10)
                    ax2.invert_yaxis()
                    ax2.spines['top'].set_visible(False)
                    ax2.spines['right'].set_visible(False)
                    ax2.spines['left'].set_color('#334155')
                    ax2.spines['bottom'].set_color('#334155')
                    ax2.xaxis.grid(True, linestyle='--', alpha=0.3, color='#94a3b8')
                    ax2.set_axisbelow(True)
                    
                    st.pyplot(fig2)
                else:
                    st.info("Dados de faturamento insuficientes para gerar o ranking.")
                    
        st.write("")
        st.markdown("### 📜 Detalhamento Histórico de Todas as OSs")
        st.dataframe(df_vendas, use_container_width=True, hide_index=True)
        
    else:
        st.info("Nenhuma ordem de serviço lançada para o cálculo de desempenho financeiro.")
