"""
Sistema Modular de Conversão e Dashboard de NF-e
Arquivo: app.py
"""
import streamlit as st
import pandas as pd
from io import BytesIO
import base64
import os

# Importa módulos customizados
import nfe_parser
import dashboard_logic

# Configuração da página
st.set_page_config(
    page_title="Sistema de NF-e",
    page_icon="logo.png",  # Usa o logo como favicon
    layout="wide"
)

# Inicializa session_state para armazenar DataFrame
if 'df_processado' not in st.session_state:
    st.session_state.df_processado = pd.DataFrame()

# Cabeçalho com logo clicável
if os.path.exists("logo.png"):
    col_logo, col_title = st.columns([1, 8])
    
    with col_logo:
        # Lê o arquivo da imagem e converte para base64
        with open("logo.png", "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        
        # Cria link clicável com o logo usando HTML
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
    # Se não houver logo, exibe título normal
    st.title("📊 Sistema de Conversão e Dashboard de NF-e")

st.markdown("---")

# Cria as abas
tab1, tab2 = st.tabs(["🔄 Conversor XML → XLSX", "📈 Dashboard"])

# ==================== ABA 1: CONVERSOR ====================
with tab1:
    st.header("Conversor de NF-e (XML para XLSX)")
    
    # Divisão em duas colunas: filtros e upload
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Filtros de Campos")
        
        # Dicionário para armazenar seleções
        selected_fields = {}
        
        # Grupo 1: Identificação e Protocolo
        with st.expander("🔍 Identificação e Protocolo", expanded=True):
            selected_fields['Chave de Acesso'] = st.checkbox('Chave de Acesso', value=True)
            selected_fields['Número da NF'] = st.checkbox('Número da NF', value=True)
            selected_fields['Série'] = st.checkbox('Série')
            selected_fields['Data e Hora de Emissão'] = st.checkbox('Data e Hora de Emissão', value=True)
            selected_fields['Natureza da Operação'] = st.checkbox('Natureza da Operação')
            selected_fields['Status do Protocolo'] = st.checkbox('Status do Protocolo')
        
        # Grupo 2: Emitente e Destinatário
        with st.expander("👥 Emitente e Destinatário", expanded=False):
            selected_fields['CNPJ do Emitente'] = st.checkbox('CNPJ do Emitente')
            selected_fields['Razão Social Emitente'] = st.checkbox('Razão Social Emitente', value=True)
            selected_fields['CNPJ do Destinatário'] = st.checkbox('CNPJ do Destinatário')
            selected_fields['Razão Social Destinatário'] = st.checkbox('Razão Social Destinatário')
            selected_fields['Inscrição Estadual Destinatário'] = st.checkbox('Inscrição Estadual Destinatário')
        
        # Grupo 3: Detalhes dos Itens
        with st.expander("📦 Detalhes dos Itens", expanded=False):
            selected_fields['Número do Item'] = st.checkbox('Número do Item')
            selected_fields['Descrição do Produto'] = st.checkbox('Descrição do Produto')
            selected_fields['CFOP do Item'] = st.checkbox('CFOP do Item')
            selected_fields['Quantidade Comercial'] = st.checkbox('Quantidade Comercial')
            selected_fields['Valor Unitário'] = st.checkbox('Valor Unitário')
        
        # Grupo 4: Totais e Impostos
        with st.expander("💰 Totais e Impostos", expanded=False):
            selected_fields['Valor Total da NF'] = st.checkbox('Valor Total da NF', value=True)
            selected_fields['Valor Total dos Produtos'] = st.checkbox('Valor Total dos Produtos')
            selected_fields['Valor Total do ICMS'] = st.checkbox('Valor Total do ICMS')
            selected_fields['Valor Total do IPI'] = st.checkbox('Valor Total do IPI')
    
    with col2:
        st.subheader("Upload de Arquivos")
        
        # Upload de arquivos
        uploaded_files = st.file_uploader(
            "Selecione arquivos XML ou ZIP contendo NF-e",
            type=['xml', 'zip'],
            accept_multiple_files=True,
            help="Você pode fazer upload de múltiplos arquivos XML ou arquivos ZIP contendo XMLs"
        )
        
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} arquivo(s) carregado(s)")
            
            # Botão para processar
            if st.button("🚀 Processar Arquivos", type="primary"):
                with st.spinner("Processando arquivos XML..."):
                    try:
                        # Chama função de processamento
                        df_result = nfe_parser.process_nfe_files(uploaded_files, selected_fields)
                        
                        if df_result.empty:
                            st.warning("⚠️ Nenhum dado foi extraído. Verifique os arquivos e os filtros selecionados.")
                        else:
                            st.session_state.df_processado = df_result
                            st.success(f"✅ Processamento concluído! {len(df_result)} registro(s) extraído(s).")
                    except Exception as e:
                        st.error(f"❌ Erro ao processar arquivos: {str(e)}")
        
        # Exibe resultado se houver dados processados
        if not st.session_state.df_processado.empty:
            st.subheader("📊 Dados Extraídos")
            st.dataframe(st.session_state.df_processado, use_container_width=True, height=400)
            
            # Botão de download
            st.subheader("💾 Download")
            
            # Converte DataFrame para CSV
            csv = st.session_state.df_processado.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name="nfe_consolidado.csv",
                mime="text/csv",
                help="Baixar dados em formato CSV"
            )
            
            # Converte DataFrame para Excel
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

# ==================== ABA 2: DASHBOARD ====================
with tab2:
    st.header("Dashboard de Análise de NF-e")
    
    # Verifica se há dados processados
    if st.session_state.df_processado.empty:
        st.info("ℹ️ Nenhum dado disponível. Por favor, processe arquivos na aba 'Conversor XML → XLSX' primeiro.")
    else:
        df_dashboard = st.session_state.df_processado.copy()
        
        # Filtros do Dashboard
        st.subheader("🔎 Filtros")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            # Filtro por Emitente
            if 'CNPJ do Emitente' in df_dashboard.columns:
                emitentes = df_dashboard['CNPJ do Emitente'].dropna().unique().tolist()
                if emitentes:
                    selected_emitentes = st.multiselect(
                        "Filtrar por CNPJ do Emitente",
                        options=emitentes,
                        default=emitentes
                    )
                    if selected_emitentes:
                        df_dashboard = df_dashboard[df_dashboard['CNPJ do Emitente'].isin(selected_emitentes)]
        
        with col_f2:
            # Filtro por Natureza da Operação
            if 'Natureza da Operação' in df_dashboard.columns:
                naturezas = df_dashboard['Natureza da Operação'].dropna().unique().tolist()
                if naturezas:
                    selected_naturezas = st.multiselect(
                        "Filtrar por Natureza da Operação",
                        options=naturezas,
                        default=naturezas
                    )
                    if selected_naturezas:
                        df_dashboard = df_dashboard[df_dashboard['Natureza da Operação'].isin(selected_naturezas)]
        
        st.markdown("---")
        
        # KPIs
        st.subheader("📊 Indicadores Principais")
        kpis = dashboard_logic.calculate_kpis(df_dashboard)
        
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        
        with col_kpi1:
            st.metric(
                label="💰 Valor Total Faturado",
                value=f"R$ {kpis['total_faturado']:,.2f}",
                help="Soma do valor total de todas as NF-e processadas"
            )
        
        with col_kpi2:
            st.metric(
                label="📄 Total de NF-e",
                value=f"{kpis['total_nfe']:,}",
                help="Número de notas fiscais processadas"
            )
        
        with col_kpi3:
            st.metric(
                label="📦 Média de Itens/NF",
                value=f"{kpis['media_itens']:.1f}",
                help="Média de itens por nota fiscal"
            )
        
        st.markdown("---")
        
        # Gráficos
        st.subheader("📈 Visualizações")
        
        # Gráfico 1: Tendência de Faturamento
        st.plotly_chart(
            dashboard_logic.create_faturamento_trend(df_dashboard),
            use_container_width=True
        )
        
        # Linha com 2 gráficos lado a lado
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Gráfico 2: Top 10 Produtos
            st.plotly_chart(
                dashboard_logic.create_top_products_chart(df_dashboard),
                use_container_width=True
            )
        
        with col_g2:
            # Gráfico 3: Distribuição por Natureza
            st.plotly_chart(
                dashboard_logic.create_natureza_pie_chart(df_dashboard),
                use_container_width=True
            )

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Sistema de Conversão e Dashboard de NF-e | Desenvolvido com Streamlit
    </div>
    """,
    unsafe_allow_html=True
)