"""
Sistema Modular de Conversão e Dashboard de NF-e
Versão FINAL - 100% conforme leiaute oficial
Arquivo: app.py - Refatorado com boas práticas
"""
import streamlit as st
import pandas as pd
from io import BytesIO
import base64
import os
from pathlib import Path

# Importa módulos customizados
import nfe_parser
import dashboard_logic

# Importa PIL para o ícone
try:
    from PIL import Image
except ImportError:
    Image = None

# ============================================
# CONSTANTES
# ============================================
PAGE_TITLE = "TRR Smart Converter"
PAGE_ICON_PATH = "logo.png"
LAYOUT = "wide"

# ============================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================
def setup_page():
    """Configura parâmetros iniciais da página Streamlit."""
    page_config = {
        "page_title": PAGE_TITLE,
        "layout": LAYOUT,
        "initial_sidebar_state": "collapsed"
    }
    
    # Adiciona ícone se existir
    if Image and Path(PAGE_ICON_PATH).exists():
        try:
            icon = Image.open(PAGE_ICON_PATH)
            page_config["page_icon"] = icon
        except Exception:
            pass
    
    st.set_page_config(**page_config)


# ============================================
# TEMA CSS - Separado em arquivo de estilo
# ============================================
def get_custom_css():
    """Retorna CSS customizado como string."""
    return """
    <style>
    /* ========================================
       IMPORTAÇÕES E RESET
    ======================================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        box-sizing: border-box;
    }
    
    /* ========================================
       LAYOUT PRINCIPAL
    ======================================== */
    .stApp { 
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .main .block-container {
        max-width: 1400px;
        padding: 2rem 3rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(27, 0, 255, 0.08);
        margin: 2rem auto;
    }
    
    /* ========================================
       TIPOGRAFIA
    ======================================== */
    h1 {
        color: #1B00FF !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        text-align: center;
        margin-bottom: 1rem !important;
    }
    
    h2 {
        color: #2C3E50 !important;
        font-weight: 600 !important;
        font-size: 1.75rem !important;
        border-left: 4px solid #1B00FF;
        padding-left: 1rem;
        margin: 2rem 0 1rem 0 !important;
    }
    
    h3 {
        color: #34495E !important;
        font-weight: 600 !important;
        font-size: 1.3rem !important;
        margin-top: 1.5rem !important;
    }
    
    /* ========================================
       COMPONENTES - TABS
    ======================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px;
        color: #6c757d;
        font-weight: 500;
        padding: 0 24px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1B00FF 0%, #5B3FFF 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(27, 0, 255, 0.3);
    }
    
    /* ========================================
       COMPONENTES - FILE UPLOADER
    ======================================== */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 2px dashed #1B00FF;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(27, 0, 255, 0.08);
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        box-shadow: 0 8px 24px rgba(27, 0, 255, 0.15);
        transform: translateY(-2px);
    }
    
    /* ========================================
       COMPONENTES - BOTÕES
    ======================================== */
    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1B00FF 0%, #5B3FFF 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(27, 0, 255, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        box-shadow: 0 6px 20px rgba(27, 0, 255, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* ========================================
       COMPONENTES - MÉTRICAS
    ======================================== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        box-shadow: 0 8px 24px rgba(27, 0, 255, 0.12);
        transform: translateY(-4px);
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1B00FF !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
    }
    
    [data-testid="stMetric"] label {
        color: #6c757d !important;
        font-weight: 600 !important;
    }
    
    /* ========================================
       COMPONENTES - EXPANDERS
    ======================================== */
    [data-testid="stExpander"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        margin: 0.5rem 0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    [data-testid="stExpander"] summary {
        font-weight: 600 !important;
        color: #1B00FF !important;
        padding: 0.75rem 1rem !important;
        border-radius: 12px !important;
    }

    [data-testid="stExpander"] > div:nth-child(2) {
        padding: 0.75rem 1rem !important;
    }

    /* ========================================
       COMPONENTES - CHECKBOXES (ESTILO PADRÃO)
    ======================================== */
    /* Removido para evitar conflitos - usando estilo nativo do Streamlit */

    /* ========================================
       COMPONENTES - MULTISELECT
    ======================================== */
    [data-testid="stMultiSelect"] {
        margin: 0.5rem 0 !important;
        min-height: auto !important;
    }

    [data-testid="stMultiSelect"] label {
        margin-bottom: 0.4rem !important;
    }
    
    [data-baseweb="tag"] {
        background-color: #1B00FF !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }
    
    /* ========================================
       COMPONENTES - ALERTAS
    ======================================== */
    .stAlert {
        border-radius: 12px;
        border-left-width: 4px;
        padding: 1rem 1.25rem;
    }
    
    /* ========================================
       COMPONENTES - DATAFRAME
    ======================================== */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    /* ========================================
       SCROLLBAR CUSTOMIZADO
    ======================================== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f3f5;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #1B00FF 0%, #5B3FFF 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5B3FFF 0%, #1B00FF 100%);
    }
    
    /* ========================================
       RESPONSIVIDADE MOBILE
    ======================================== */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
            margin: 1rem;
        }
        
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        [data-testid="stExpander"] summary {
            padding: 0.6rem 0.75rem !important;
            font-size: 0.9rem !important;
        }
        
        [data-testid="stExpander"] > div:nth-child(2) {
            padding: 0.75rem !important;
        }
        
        [data-testid="stCheckbox"] {
            padding: 0.3rem 0 !important;
        }
        
        [data-testid="stCheckbox"] label {
            font-size: 0.9rem !important;
        }
    }
    
    /* ========================================
       OCULTA ELEMENTOS PADRÃO
    ======================================== */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """


def apply_custom_theme():
    """Aplica tema CSS customizado."""
    st.markdown(get_custom_css(), unsafe_allow_html=True)


# ============================================
# COMPONENTES DE UI
# ============================================
def render_logo():
    """Renderiza logo e título da aplicação."""
    if Path(PAGE_ICON_PATH).exists():
        col_logo, col_title = st.columns([1, 8])
        
        with col_logo:
            with open(PAGE_ICON_PATH, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()
            
            st.markdown(
                f'''
                <a href="https://www.instagram.com/trr_contabilidade/" target="_blank">
                    <img src="data:image/png;base64,{img_base64}" width="80" 
                         style="cursor: pointer; transition: opacity 0.3s;" 
                         onmouseover="this.style.opacity='0.7'" 
                         onmouseout="this.style.opacity='1'"
                         alt="TRR Contabilidade">
                </a>
                ''',
                unsafe_allow_html=True
            )
        
        with col_title:
            st.title("📊 Sistema de Conversão e Dashboard de NF-e")
    else:
        st.title("📊 Sistema de Conversão e Dashboard de NF-e")


def render_field_filters():
    """Renderiza filtros de campos para seleção."""
    st.subheader("Filtros de Campos")
    
    # Perfis rápidos
    st.markdown("**⚡ Perfis Rápidos:**")
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        perfil_basico = st.button("🔹 Básico", help="Campos essenciais")
    with col_p2:
        perfil_completo = st.button("🔸 Completo", help="Todos os campos")
    with col_p3:
        perfil_limpar = st.button("⭕ Limpar", help="Desmarcar todos")
    
    selected_fields = {}
    
    # Grupo B/A: Identificação
    with st.expander("🔍 Identificação e Protocolo (Grupo B/A)", expanded=True):
        selected_fields['Chave de Acesso'] = st.checkbox('Chave de Acesso (ID A03)', value=True if not perfil_limpar else False)
        selected_fields['Número da NF'] = st.checkbox('Número da NF (ID B08)', value=True if not perfil_limpar else False)
        selected_fields['Série'] = st.checkbox('Série (ID B07)', value=perfil_completo)
        selected_fields['Data e Hora de Emissão'] = st.checkbox('Data e Hora de Emissão (ID B09)', value=True if not perfil_limpar else False)
        selected_fields['Natureza da Operação'] = st.checkbox('Natureza da Operação (ID B05)', value=True if not perfil_limpar else False)
        selected_fields['Modelo'] = st.checkbox('Modelo (ID B06)', value=perfil_completo)
        selected_fields['Versão'] = st.checkbox('Versão (ID A02)', value=perfil_completo)
        selected_fields['Status do Protocolo'] = st.checkbox('Status do Protocolo', value=perfil_completo)
    
    # Grupo C: Emitente
    with st.expander("👤 Emitente (Grupo C)", expanded=False):
        selected_fields['CNPJ do Emitente'] = st.checkbox('CNPJ/CPF do Emitente (ID C02/C02a)', value=perfil_completo)
        selected_fields['Razão Social Emitente'] = st.checkbox('Razão Social (ID C03)', value=True if not perfil_limpar else False)
        selected_fields['Nome Fantasia Emitente'] = st.checkbox('Nome Fantasia (ID C04)', value=perfil_completo)
    
    # Grupo E: Destinatário
    with st.expander("👥 Destinatário (Grupo E)", expanded=False):
        selected_fields['CNPJ do Destinatário'] = st.checkbox('CNPJ/CPF Destinatário (ID E02/E03)', value=perfil_completo)
        selected_fields['Razão Social Destinatário'] = st.checkbox('Razão Social (ID E04)', value=perfil_completo)
        selected_fields['Inscrição Estadual Destinatário'] = st.checkbox('Inscrição Estadual (ID E17)', value=perfil_completo)
    
    # Grupo I: Detalhes dos Produtos
    with st.expander("📦 Detalhes dos Produtos (Grupo I)", expanded=True):
        st.caption("**Campos Essenciais do Produto**")
        selected_fields['Número do Item'] = st.checkbox('Nº Item (ID H02)', value=True if not perfil_limpar else False)
        selected_fields['Cód. Produto'] = st.checkbox('Cód. Produto (ID I02)', value=True if not perfil_limpar else False)
        selected_fields['Código EAN'] = st.checkbox('Código EAN/GTIN (ID I03)', value=perfil_completo)
        selected_fields['Descrição do Produto'] = st.checkbox('Descrição do Produto (ID I04)', value=True if not perfil_limpar else False)
        selected_fields['NCM'] = st.checkbox('NCM (ID I05)', value=True if not perfil_limpar else False)
        selected_fields['CEST'] = st.checkbox('CEST (ID I08)', value=perfil_completo)
        selected_fields['CFOP do Item'] = st.checkbox('CFOP (ID I09)', value=True if not perfil_limpar else False)
        
        st.caption("**Quantidades e Valores**")
        selected_fields['Unidade Comercial'] = st.checkbox('Unidade Comercial (ID I10)', value=True if not perfil_limpar else False)
        selected_fields['Quantidade Comercial'] = st.checkbox('Quantidade Comercial (ID I11)', value=True if not perfil_limpar else False)
        selected_fields['Valor Unitário'] = st.checkbox('Valor Unitário (ID I12)', value=True if not perfil_limpar else False)
        selected_fields['Valor Total Item'] = st.checkbox('Valor Total Item (ID I13)', value=True if not perfil_limpar else False)
    
    # Grupo N: ICMS
    with st.expander("💸 ICMS por Item (Grupo N)", expanded=False):
        st.caption("**Campos de ICMS (todos os CST)**")
        selected_fields['Origem da Mercadoria'] = st.checkbox('Origem da Mercadoria (ID N11)', value=perfil_completo)
        selected_fields['CST ICMS'] = st.checkbox('CST ICMS (ID N12)', value=perfil_completo)
        selected_fields['Modalidade BC ICMS'] = st.checkbox('Modalidade BC (ID N13)', value=perfil_completo)
        selected_fields['Base Cálculo ICMS'] = st.checkbox('Base de Cálculo ICMS (ID N15)', value=True if perfil_basico or perfil_completo else False)
        selected_fields['Alíquota ICMS'] = st.checkbox('Alíquota ICMS % (ID N16)', value=True if perfil_basico or perfil_completo else False)
        selected_fields['Valor ICMS'] = st.checkbox('Valor ICMS (ID N17)', value=True if perfil_basico or perfil_completo else False)
    
    # Grupos O, Q, S: Outros Impostos
    with st.expander("📊 Outros Impostos (Grupos O/Q/S)", expanded=False):
        selected_fields['Valor IPI'] = st.checkbox('Valor IPI (Grupo O)', value=perfil_completo)
        selected_fields['Valor PIS'] = st.checkbox('Valor PIS (Grupo Q)', value=perfil_completo)
        selected_fields['Valor COFINS'] = st.checkbox('Valor COFINS (Grupo S)', value=perfil_completo)
    
    # Grupo NA: ICMSUFDest - DIFAL
    with st.expander("⚖️ DIFAL - Grupo ICMSUFDest (Grupo NA)", expanded=False):
        st.caption("**📌 Partilha do ICMS Interestadual**")
        st.info("Preencher apenas em operações interestaduais destinadas a consumidor final não contribuinte.")
        
        selected_fields['BC ICMS UF Destino'] = st.checkbox('BC ICMS UF Destino (ID NA03)', value=perfil_completo)
        selected_fields['Alíquota Interna UF Destino'] = st.checkbox('Alíquota Interna UF Destino % (ID NA07)', value=perfil_completo)
        selected_fields['Alíquota Interestadual'] = st.checkbox('Alíquota Interestadual % (ID NA09)', value=perfil_completo)
        selected_fields['Percentual Partilha ICMS'] = st.checkbox(
            'Percentual Partilha ICMS % (ID NA11) ⚠️',
            value=perfil_completo,
            help="CRÍTICO: Campo essencial para evitar Rejeição 699. Obrigatório quando há DIFAL."
        )
        selected_fields['Valor ICMS UF Destino'] = st.checkbox('Valor ICMS UF Destino (ID NA15)', value=perfil_completo)
        selected_fields['Valor ICMS UF Remetente'] = st.checkbox('Valor ICMS UF Remetente (ID NA17)', value=perfil_completo)
        
        st.caption("**🛡️ Fundo de Combate à Pobreza (FCP)**")
        selected_fields['BC FCP UF Destino'] = st.checkbox('BC FCP UF Destino (ID NA04)', value=perfil_completo)
        selected_fields['Percentual FCP UF Destino'] = st.checkbox('Percentual FCP UF Destino % (ID NA05)', value=perfil_completo)
        selected_fields['Valor FCP UF Destino'] = st.checkbox('Valor FCP UF Destino (ID NA13)', value=perfil_completo)
    
    # Grupo W: Totais
    with st.expander("💰 Totais da NF-e (Grupo W)", expanded=False):
        selected_fields['Valor Total da NF'] = st.checkbox('Valor Total da NF (ID W29)', value=True if not perfil_limpar else False)
        selected_fields['Valor Total dos Produtos'] = st.checkbox('Valor Total dos Produtos (ID W12)', value=perfil_completo)
        selected_fields['Valor Total do ICMS'] = st.checkbox('Valor Total do ICMS (ID W14)', value=perfil_completo)
        selected_fields['Valor Total do IPI'] = st.checkbox('Valor Total do IPI (ID W16)', value=perfil_completo)
    
    return selected_fields


def render_converter_tab():
    """Renderiza aba de conversão de XML para XLSX."""
    st.header("Conversor de NF-e (XML para XLSX)")
    
    st.info("⚠️ **IMPORTANTE**: O sistema gera **UMA LINHA POR ITEM** de produto (tag `<det>`), não por Nota Fiscal.")
    st.caption("📘 **Conforme leiaute oficial**: http://moc.sped.fazenda.pr.gov.br/Leiaute.html")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_fields = render_field_filters()
    
    with col2:
        st.subheader("Upload de Arquivos")
        
        uploaded_files = st.file_uploader(
            "Selecione arquivos XML ou ZIP contendo NF-e",
            type=['xml', 'zip'],
            accept_multiple_files=True,
            help="Você pode fazer upload de múltiplos arquivos XML ou arquivos ZIP contendo XMLs"
        )
        
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} arquivo(s) carregado(s)")
            
            if st.button("🚀 Processar Arquivos", type="primary"):
                with st.spinner("Processando arquivos XML conforme leiaute oficial..."):
                    try:
                        df_result = nfe_parser.process_nfe_files(uploaded_files, selected_fields)
                        
                        if df_result.empty:
                            st.warning("⚠️ Nenhum dado foi extraído. Verifique os arquivos e os filtros selecionados.")
                        else:
                            st.session_state.df_processado = df_result
                            
                            # Conta NF-e únicas
                            if 'Chave de Acesso' in df_result.columns:
                                num_nfe = df_result['Chave de Acesso'].nunique()
                            elif 'Número da NF' in df_result.columns:
                                num_nfe = df_result['Número da NF'].nunique()
                            else:
                                num_nfe = "N/A"
                            
                            st.success(f"✅ Processamento concluído! **{len(df_result)} item(ns)** extraído(s) de **{num_nfe} NF-e(s)**.")
                    except Exception as e:
                        st.error(f"❌ Erro ao processar arquivos: {str(e)}")
        
        if not st.session_state.df_processado.empty:
            st.subheader("📊 Dados Extraídos")
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.metric("📋 Total de Linhas (Itens)", len(st.session_state.df_processado))
            with col_info2:
                if 'Chave de Acesso' in st.session_state.df_processado.columns:
                    num_nfe = st.session_state.df_processado['Chave de Acesso'].nunique()
                    st.metric("📄 NF-e(s) Únicas", num_nfe)
            
            st.dataframe(st.session_state.df_processado, use_container_width=True, height=400)
            
            st.subheader("💾 Download")
            
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                csv = st.session_state.df_processado.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv,
                    file_name="nfe_consolidado.csv",
                    mime="text/csv",
                    help="Baixar dados em formato CSV (UTF-8 com BOM)"
                )
            
            with col_d2:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    st.session_state.df_processado.to_excel(writer, index=False, sheet_name='NF-e')
                
                st.download_button(
                    label="📥 Baixar XLSX",
                    data=buffer.getvalue(),
                    file_name="nfe_consolidado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Baixar dados em formato Excel"
                )


def render_dashboard_tab():
    """Renderiza aba de dashboard com análises."""
    st.header("Dashboard de Análise de NF-e")
    
    if st.session_state.df_processado.empty:
        st.info("ℹ️ Nenhum dado disponível. Por favor, processe arquivos na aba 'Conversor XML → XLSX' primeiro.")
        return
    
    df_dashboard = st.session_state.df_processado.copy()
    
    # Filtros inteligentes
    st.subheader("🔎 Filtros Inteligentes")
    df_dashboard = render_dashboard_filters(df_dashboard)
    
    st.markdown("---")
    
    if df_dashboard.empty:
        st.warning("⚠️ Nenhum dado disponível com os filtros selecionados. Ajuste os filtros acima.")
        return
    
    # KPIs
    st.subheader("📊 Indicadores Principais")
    render_kpis(df_dashboard)
    
    st.markdown("---")
    
    # Gráficos
    st.subheader("📈 Visualizações")
    render_charts(df_dashboard)


def render_dashboard_filters(df):
    """Renderiza filtros do dashboard e retorna DataFrame filtrado."""
    filtros_disponiveis = [
        col for col in ['CNPJ do Emitente', 'Razão Social Emitente', 'CNPJ do Destinatário',
                       'Razão Social Destinatário', 'Natureza da Operação', 'CFOP do Item',
                       'Descrição do Produto']
        if col in df.columns
    ]
    
    if not filtros_disponiveis:
        st.warning("⚠️ Nenhum campo de filtro disponível.")
        return df
    
    with st.expander("⚙️ **Configurar Filtros**", expanded=True):
        st.info("💡 **Dica**: Os filtros se adaptam automaticamente aos campos que você processou.")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            # Filtro Emitente
            if 'CNPJ do Emitente' in df.columns:
                emitentes = sorted(df['CNPJ do Emitente'].dropna().unique().tolist())
                if emitentes:
                    st.markdown("**📤 CNPJ do Emitente**")
                    selected_emitentes = st.multiselect(
                        "Selecione:", options=emitentes, default=emitentes,
                        key="filter_emit", label_visibility="collapsed"
                    )
                    if selected_emitentes:
                        df = df[df['CNPJ do Emitente'].isin(selected_emitentes)]
            
            elif 'Razão Social Emitente' in df.columns:
                emit_razao = sorted(df['Razão Social Emitente'].dropna().unique().tolist())
                if emit_razao:
                    st.markdown("**📤 Razão Social Emitente**")
                    selected_emit_razao = st.multiselect(
                        "Selecione:", options=emit_razao, default=emit_razao,
                        key="filter_emit_razao", label_visibility="collapsed"
                    )
                    if selected_emit_razao:
                        df = df[df['Razão Social Emitente'].isin(selected_emit_razao)]
            
            # Filtro Natureza da Operação
            if 'Natureza da Operação' in df.columns:
                naturezas = sorted(df['Natureza da Operação'].dropna().unique().tolist())
                if naturezas:
                    st.markdown("**📋 Natureza da Operação**")
                    selected_naturezas = st.multiselect(
                        "Selecione:", options=naturezas, default=naturezas,
                        key="filter_nat", label_visibility="collapsed"
                    )
                    if selected_naturezas:
                        df = df[df['Natureza da Operação'].isin(selected_naturezas)]
        
        with col_f2:
            # Filtro Destinatário
            if 'CNPJ do Destinatário' in df.columns:
                destinatarios = sorted(df['CNPJ do Destinatário'].dropna().unique().tolist())
                if destinatarios:
                    st.markdown("**📥 CNPJ do Destinatário**")
                    selected_destinatarios = st.multiselect(
                        "Selecione:", options=destinatarios, default=destinatarios,
                        key="filter_dest", label_visibility="collapsed"
                    )
                    if selected_destinatarios:
                        df = df[df['CNPJ do Destinatário'].isin(selected_destinatarios)]
            
            elif 'Razão Social Destinatário' in df.columns:
                dest_razao = sorted(df['Razão Social Destinatário'].dropna().unique().tolist())
                if dest_razao:
                    st.markdown("**📥 Razão Social Destinatário**")
                    selected_dest_razao = st.multiselect(
                        "Selecione:", options=dest_razao, default=dest_razao,
                        key="filter_dest_razao", label_visibility="collapsed"
                    )
                    if selected_dest_razao:
                        df = df[df['Razão Social Destinatário'].isin(selected_dest_razao)]
            
            # Filtro CFOP
            if 'CFOP do Item' in df.columns:
                cfops = sorted(df['CFOP do Item'].dropna().unique().tolist())
                if cfops:
                    st.markdown("**🔢 CFOP**")
                    selected_cfops = st.multiselect(
                        "Selecione:", options=cfops, default=cfops,
                        key="filter_cfop", label_visibility="collapsed"
                    )
                    if selected_cfops:
                        df = df[df['CFOP do Item'].isin(selected_cfops)]
    
    return df


def render_kpis(df):
    """Renderiza indicadores principais (KPIs)."""
    kpis = dashboard_logic.calculate_kpis(df)
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    with col_kpi1:
        st.metric(
            label="💰 Valor Total Faturado",
            value=f"R$ {kpis['total_faturado']:,.2f}",
            help="Soma do valor total de todas as NF-e processadas (sem duplicação)"
        )
    
    with col_kpi2:
        st.metric(
            label="📄 Total de NF-e",
            value=f"{kpis['total_nfe']:,}",
            help="Número de notas fiscais únicas processadas"
        )
    
    with col_kpi3:
        st.metric(
            label="📦 Média de Itens/NF",
            value=f"{kpis['media_itens']:.1f}",
            help="Média de itens por nota fiscal"
        )


def render_charts(df):
    """Renderiza gráficos de análise."""
    # Gráfico de tendência (largura completa)
    st.plotly_chart(
        dashboard_logic.create_faturamento_trend(df),
        use_container_width=True
    )
    
    # Dois gráficos lado a lado
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.plotly_chart(
            dashboard_logic.create_top_products_chart(df),
            use_container_width=True
        )
    
    with col_g2:
        st.plotly_chart(
            dashboard_logic.create_natureza_pie_chart(df),
            use_container_width=True
        )


def render_footer():
    """Renderiza rodapé da aplicação."""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; padding: 20px;'>
            <p style='color: #666; margin-bottom: 15px; font-size: 16px;'>
                <strong>Sistema de Conversão e Dashboard de NF-e</strong><br>
                <span style='font-size: 12px;'>Conforme Leiaute Oficial NT 2025.001 v.1.02</span>
            </p>
            <div style='display: flex; justify-content: center; align-items: center; gap: 30px; flex-wrap: wrap;'>
                <a href="https://trrcontabil.com" target="_blank" 
                   style='color: #1f77b4; text-decoration: none; font-size: 14px;'>
                    🌐 trrcontabil.com
                </a>
                <a href="https://www.instagram.com/trr_contabilidade/" target="_blank" 
                   style='color: #E4405F; text-decoration: none; font-size: 14px;'>
                    📷 @trr_contabilidade
                </a>
                <a href="https://wa.me/5591992412788" target="_blank" 
                   style='color: #25D366; text-decoration: none; font-size: 14px;'>
                    📞 (91) 99241-2788
                </a>
            </div>
            <p style='color: #999; margin-top: 15px; font-size: 12px;'>
                Desenvolvido com Streamlit ❤️ | Referência: 
                <a href="http://moc.sped.fazenda.pr.gov.br/Leiaute.html" target="_blank" style='color: #999;'>
                    Leiaute Oficial
                </a>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================
# FUNÇÃO PRINCIPAL
# ============================================
def main():
    """Função principal da aplicação."""
    # Configuração inicial
    setup_page()
    apply_custom_theme()
    
    # Inicializa session_state
    if 'df_processado' not in st.session_state:
        st.session_state.df_processado = pd.DataFrame()
    
    # Cabeçalho
    render_logo()
    st.markdown("---")
    
    # Abas principais
    tab1, tab2 = st.tabs(["🔄 Conversor XML → XLSX", "📈 Dashboard"])
    
    with tab1:
        render_converter_tab()
    
    with tab2:
        render_dashboard_tab()
    
    # Rodapé
    render_footer()


# ============================================
# PONTO DE ENTRADA
# ============================================
if __name__ == "__main__":
    main()