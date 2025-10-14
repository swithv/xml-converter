"""
Módulo de lógica do Dashboard - KPIs e Gráficos
Arquivo: dashboard_logic.py
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any


def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula os KPIs principais do dashboard
    """
    kpis = {
        'total_faturado': 0.0,
        'total_nfe': 0,
        'media_itens': 0.0
    }
    
    if df.empty:
        return kpis
    
    # Valor Total Faturado
    if 'Valor Total da NF' in df.columns:
        try:
            df['Valor Total da NF'] = pd.to_numeric(df['Valor Total da NF'], errors='coerce')
            # Conta valores únicos por Chave de Acesso ou Número da NF para evitar duplicação
            if 'Chave de Acesso' in df.columns:
                kpis['total_faturado'] = df.groupby('Chave de Acesso')['Valor Total da NF'].first().sum()
            elif 'Número da NF' in df.columns:
                kpis['total_faturado'] = df.groupby('Número da NF')['Valor Total da NF'].first().sum()
            else:
                kpis['total_faturado'] = df['Valor Total da NF'].sum()
        except Exception:
            pass
    
    # Total de NF-e Processadas
    if 'Chave de Acesso' in df.columns:
        kpis['total_nfe'] = df['Chave de Acesso'].nunique()
    elif 'Número da NF' in df.columns:
        kpis['total_nfe'] = df['Número da NF'].nunique()
    else:
        kpis['total_nfe'] = len(df)
    
    # Média de Itens por NF
    if 'Número do Item' in df.columns:
        if 'Chave de Acesso' in df.columns:
            itens_por_nf = df.groupby('Chave de Acesso')['Número do Item'].count()
            kpis['media_itens'] = itens_por_nf.mean()
        elif 'Número da NF' in df.columns:
            itens_por_nf = df.groupby('Número da NF')['Número do Item'].count()
            kpis['media_itens'] = itens_por_nf.mean()
    
    return kpis


def create_faturamento_trend(df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de linha com tendência de faturamento
    """
    if df.empty or 'Data e Hora de Emissão' not in df.columns or 'Valor Total da NF' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para gerar o gráfico",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Tendência de Faturamento')
        return fig
    
    try:
        # Prepara dados
        df_temp = df.copy()
        
        # Converte para datetime de forma robusta
        df_temp['Data e Hora de Emissão'] = pd.to_datetime(df_temp['Data e Hora de Emissão'], errors='coerce')
        
        # Remove linhas onde a conversão falhou
        df_temp = df_temp.dropna(subset=['Data e Hora de Emissão'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhuma data válida encontrada",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Tendência de Faturamento')
            return fig
        
        df_temp['Valor Total da NF'] = pd.to_numeric(df_temp['Valor Total da NF'], errors='coerce')
        
        # Remove duplicatas por NF
        if 'Chave de Acesso' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Chave de Acesso'])
        elif 'Número da NF' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Número da NF'])
        
        # Extrai apenas a data (sem hora) - método mais seguro
        # Usa apply com lambda para evitar problemas de tipo
        df_temp['Data'] = df_temp['Data e Hora de Emissão'].apply(lambda x: x.date() if pd.notnull(x) else None)
        
        # Remove linhas com Data None
        df_temp = df_temp.dropna(subset=['Data'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhuma data válida após processamento",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Tendência de Faturamento')
            return fig
        
        # Agrupa por data
        df_grouped = df_temp.groupby('Data')['Valor Total da NF'].sum().reset_index()
        df_grouped = df_grouped.sort_values('Data')
        
        # Cria gráfico
        fig = px.line(df_grouped, x='Data', y='Valor Total da NF',
                      title='Tendência de Faturamento',
                      labels={'Valor Total da NF': 'Valor (R$)', 'Data': 'Data de Emissão'})
        
        fig.update_traces(line_color='#1f77b4', line_width=3)
        fig.update_layout(hovermode='x unified')
        
        return fig
        
    except Exception as e:
        # Em caso de erro, retorna gráfico vazio com mensagem
        fig = go.Figure()
        fig.add_annotation(text=f"Erro ao processar datas: {str(e)}",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Tendência de Faturamento')
        return fig


def create_top_products_chart(df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de barras com Top 10 produtos por quantidade
    """
    if df.empty or 'Descrição do Produto' not in df.columns or 'Quantidade Comercial' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para gerar o gráfico",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Top 10 Produtos por Quantidade')
        return fig
    
    try:
        # Prepara dados
        df_temp = df.copy()
        df_temp['Quantidade Comercial'] = pd.to_numeric(df_temp['Quantidade Comercial'], errors='coerce')
        
        # Remove valores nulos
        df_temp = df_temp.dropna(subset=['Quantidade Comercial', 'Descrição do Produto'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhum produto válido encontrado",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Top 10 Produtos por Quantidade')
            return fig
        
        # Agrupa por produto
        df_grouped = df_temp.groupby('Descrição do Produto')['Quantidade Comercial'].sum().reset_index()
        df_grouped = df_grouped.sort_values('Quantidade Comercial', ascending=False).head(10)
        df_grouped = df_grouped.sort_values('Quantidade Comercial', ascending=True)  # Para exibir barras crescentes
        
        # Cria gráfico
        fig = px.bar(df_grouped, x='Quantidade Comercial', y='Descrição do Produto',
                     orientation='h',
                     title='Top 10 Produtos por Quantidade',
                     labels={'Quantidade Comercial': 'Quantidade', 'Descrição do Produto': 'Produto'})
        
        fig.update_traces(marker_color='#2ca02c')
        fig.update_layout(height=500)
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Erro ao processar produtos: {str(e)}",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Top 10 Produtos por Quantidade')
        return fig


def create_natureza_pie_chart(df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de pizza com distribuição por Natureza da Operação
    """
    if df.empty or 'Natureza da Operação' not in df.columns or 'Valor Total da NF' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para gerar o gráfico",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Distribuição de Faturamento por Natureza da Operação')
        return fig
    
    try:
        # Prepara dados
        df_temp = df.copy()
        df_temp['Valor Total da NF'] = pd.to_numeric(df_temp['Valor Total da NF'], errors='coerce')
        
        # Remove valores nulos
        df_temp = df_temp.dropna(subset=['Valor Total da NF', 'Natureza da Operação'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhuma natureza de operação válida encontrada",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Distribuição de Faturamento por Natureza da Operação')
            return fig
        
        # Remove duplicatas por NF
        if 'Chave de Acesso' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Chave de Acesso'])
        elif 'Número da NF' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Número da NF'])
        
        # Agrupa por natureza
        df_grouped = df_temp.groupby('Natureza da Operação')['Valor Total da NF'].sum().reset_index()
        
        # Cria gráfico
        fig = px.pie(df_grouped, values='Valor Total da NF', names='Natureza da Operação',
                     title='Distribuição de Faturamento por Natureza da Operação')
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Erro ao processar naturezas: {str(e)}",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Distribuição de Faturamento por Natureza da Operação')
        return fig