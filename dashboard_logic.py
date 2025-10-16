"""
Módulo de lógica do Dashboard - KPIs e Gráficos
Versão FINAL - Atualizado para granularidade por item
Arquivo: dashboard_logic.py
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from datetime import datetime, date


def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula os KPIs principais do dashboard.
    IMPORTANTE: Considera que df tem UMA LINHA POR ITEM.
    """
    kpis = {
        'total_faturado': 0.0,
        'total_nfe': 0,
        'media_itens': 0.0
    }
    
    if df.empty:
        return kpis
    
    # Valor Total Faturado (sem duplicar NF-e)
    if 'Valor Total da NF' in df.columns:
        try:
            df_temp = df.copy()
            df_temp['Valor Total da NF'] = pd.to_numeric(df_temp['Valor Total da NF'], errors='coerce')
            
            # Remove duplicatas por NF-e para não somar o total múltiplas vezes
            if 'Chave de Acesso' in df_temp.columns:
                df_nfe = df_temp.drop_duplicates(subset='Chave de Acesso')
                kpis['total_faturado'] = df_nfe['Valor Total da NF'].sum()
            elif 'Número da NF' in df_temp.columns:
                df_nfe = df_temp.drop_duplicates(subset='Número da NF')
                kpis['total_faturado'] = df_nfe['Valor Total da NF'].sum()
            else:
                kpis['total_faturado'] = df_temp['Valor Total da NF'].sum()
        except Exception:
            pass
    
    # Total de NF-e Processadas (únicas)
    if 'Chave de Acesso' in df.columns:
        kpis['total_nfe'] = df['Chave de Acesso'].nunique()
    elif 'Número da NF' in df.columns:
        kpis['total_nfe'] = df['Número da NF'].nunique()
    else:
        kpis['total_nfe'] = len(df)
    
    # Média de Itens por NF
    if kpis['total_nfe'] > 0:
        total_itens = len(df)
        kpis['media_itens'] = total_itens / kpis['total_nfe']
    
    return kpis


def safe_convert_to_date(date_value):
    """Converte valor para date de forma segura."""
    try:
        if pd.isnull(date_value):
            return None
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            # Tenta converter string para datetime
            dt = pd.to_datetime(date_value, errors='coerce')
            if pd.notnull(dt):
                return dt.date()
        return None
    except Exception:
        return None


def create_faturamento_trend(df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de linha com tendência de faturamento.
    IMPORTANTE: Remove duplicatas de NF-e para não somar múltiplas vezes.
    """
    if df.empty or 'Data e Hora de Emissão' not in df.columns or 'Valor Total da NF' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para gerar o gráfico",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Tendência de Faturamento')
        return fig
    
    try:
        df_temp = df.copy()
        
        # Converte data de forma mais robusta
        df_temp['Data e Hora de Emissão'] = pd.to_datetime(df_temp['Data e Hora de Emissão'], errors='coerce')
        df_temp = df_temp.dropna(subset=['Data e Hora de Emissão'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhuma data válida encontrada",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Tendência de Faturamento')
            return fig
        
        # Converte valor
        df_temp['Valor Total da NF'] = pd.to_numeric(df_temp['Valor Total da NF'], errors='coerce')
        
        # CRÍTICO: Remove duplicatas por NF-e
        if 'Chave de Acesso' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Chave de Acesso'])
        elif 'Número da NF' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Número da NF'])
        
        # Extrai apenas a data (método robusto)
        df_temp['Data'] = df_temp['Data e Hora de Emissão'].apply(safe_convert_to_date)
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
                      title='Tendência de Faturamento (por dia)',
                      labels={'Valor Total da NF': 'Valor (R$)', 'Data': 'Data de Emissão'})
        
        fig.update_traces(line_color='#1f77b4', line_width=3)
        fig.update_layout(
            hovermode='x unified',
            xaxis_title='Data',
            yaxis_title='Faturamento (R$)',
            yaxis=dict(tickformat=',.2f')
        )
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Erro ao processar dados: {str(e)}",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Tendência de Faturamento')
        return fig


def create_top_products_chart(df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de barras com Top 10 produtos por quantidade.
    Agora funciona perfeitamente com granularidade por item.
    """
    if df.empty or 'Descrição do Produto' not in df.columns or 'Quantidade Comercial' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para gerar o gráfico",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Top 10 Produtos por Quantidade')
        return fig
    
    try:
        df_temp = df.copy()
        df_temp['Quantidade Comercial'] = pd.to_numeric(df_temp['Quantidade Comercial'], errors='coerce')
        df_temp = df_temp.dropna(subset=['Quantidade Comercial', 'Descrição do Produto'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhum produto válido encontrado",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Top 10 Produtos por Quantidade')
            return fig
        
        # Agrupa por produto (soma quantidades)
        df_grouped = df_temp.groupby('Descrição do Produto')['Quantidade Comercial'].sum().reset_index()
        df_grouped = df_grouped.sort_values('Quantidade Comercial', ascending=False).head(10)
        df_grouped = df_grouped.sort_values('Quantidade Comercial', ascending=True)
        
        # Cria gráfico
        fig = px.bar(df_grouped, x='Quantidade Comercial', y='Descrição do Produto',
                     orientation='h',
                     title='Top 10 Produtos por Quantidade',
                     labels={'Quantidade Comercial': 'Quantidade', 'Descrição do Produto': 'Produto'})
        
        fig.update_traces(marker_color='#2ca02c', hovertemplate='%{y}<br>Quantidade: %{x:,.2f}<extra></extra>')
        fig.update_layout(
            height=500,
            xaxis_title='Quantidade',
            yaxis_title='Produto',
            xaxis=dict(tickformat=',.0f')
        )
        
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
    Cria gráfico de pizza com distribuição por Natureza da Operação.
    IMPORTANTE: Remove duplicatas de NF-e para não contar múltiplas vezes.
    """
    if df.empty or 'Natureza da Operação' not in df.columns or 'Valor Total da NF' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para gerar o gráfico",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Distribuição de Faturamento por Natureza da Operação')
        return fig
    
    try:
        df_temp = df.copy()
        df_temp['Valor Total da NF'] = pd.to_numeric(df_temp['Valor Total da NF'], errors='coerce')
        df_temp = df_temp.dropna(subset=['Valor Total da NF', 'Natureza da Operação'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhuma natureza de operação válida encontrada",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Distribuição de Faturamento por Natureza da Operação')
            return fig
        
        # CRÍTICO: Remove duplicatas por NF-e
        if 'Chave de Acesso' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Chave de Acesso'])
        elif 'Número da NF' in df_temp.columns:
            df_temp = df_temp.drop_duplicates(subset=['Número da NF'])
        
        # Agrupa por natureza
        df_grouped = df_temp.groupby('Natureza da Operação')['Valor Total da NF'].sum().reset_index()
        df_grouped = df_grouped.sort_values('Valor Total da NF', ascending=False)
        
        # Cria gráfico
        fig = px.pie(df_grouped, values='Valor Total da NF', names='Natureza da Operação',
                     title='Distribuição de Faturamento por Natureza da Operação')
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}<br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
        )
        
        fig.update_layout(showlegend=True)
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Erro ao processar naturezas: {str(e)}",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Distribuição de Faturamento por Natureza da Operação')
        return fig


def create_top_products_by_value_chart(df: pd.DataFrame) -> go.Figure:
    """
    BÔNUS: Cria gráfico de barras com Top 10 produtos por VALOR.
    Útil para análise de faturamento por produto.
    """
    if df.empty or 'Descrição do Produto' not in df.columns or 'Valor Total Item' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para gerar o gráfico",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Top 10 Produtos por Valor')
        return fig
    
    try:
        df_temp = df.copy()
        df_temp['Valor Total Item'] = pd.to_numeric(df_temp['Valor Total Item'], errors='coerce')
        df_temp = df_temp.dropna(subset=['Valor Total Item', 'Descrição do Produto'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhum produto válido encontrado",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Top 10 Produtos por Valor')
            return fig
        
        # Agrupa por produto (soma valores)
        df_grouped = df_temp.groupby('Descrição do Produto')['Valor Total Item'].sum().reset_index()
        df_grouped = df_grouped.sort_values('Valor Total Item', ascending=False).head(10)
        df_grouped = df_grouped.sort_values('Valor Total Item', ascending=True)
        
        # Cria gráfico
        fig = px.bar(df_grouped, x='Valor Total Item', y='Descrição do Produto',
                     orientation='h',
                     title='Top 10 Produtos por Valor Faturado',
                     labels={'Valor Total Item': 'Valor (R$)', 'Descrição do Produto': 'Produto'})
        
        fig.update_traces(
            marker_color='#ff7f0e',
            hovertemplate='%{y}<br>Valor: R$ %{x:,.2f}<extra></extra>'
        )
        
        fig.update_layout(
            height=500,
            xaxis_title='Valor Faturado (R$)',
            yaxis_title='Produto',
            xaxis=dict(tickformat=',.2f')
        )
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Erro ao processar produtos: {str(e)}",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Top 10 Produtos por Valor')
        return fig


def create_cfop_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    BÔNUS: Cria gráfico de barras com distribuição por CFOP.
    Útil para análise fiscal.
    """
    if df.empty or 'CFOP do Item' not in df.columns or 'Valor Total Item' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para gerar o gráfico",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Distribuição por CFOP')
        return fig
    
    try:
        df_temp = df.copy()
        df_temp['Valor Total Item'] = pd.to_numeric(df_temp['Valor Total Item'], errors='coerce')
        df_temp = df_temp.dropna(subset=['Valor Total Item', 'CFOP do Item'])
        
        if df_temp.empty:
            fig = go.Figure()
            fig.add_annotation(text="Nenhum CFOP válido encontrado",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title='Distribuição por CFOP')
            return fig
        
        # Agrupa por CFOP
        df_grouped = df_temp.groupby('CFOP do Item')['Valor Total Item'].sum().reset_index()
        df_grouped = df_grouped.sort_values('Valor Total Item', ascending=False).head(10)
        df_grouped = df_grouped.sort_values('Valor Total Item', ascending=True)
        
        # Cria gráfico
        fig = px.bar(df_grouped, x='Valor Total Item', y='CFOP do Item',
                     orientation='h',
                     title='Top 10 CFOP por Valor',
                     labels={'Valor Total Item': 'Valor (R$)', 'CFOP do Item': 'CFOP'})
        
        fig.update_traces(
            marker_color='#9467bd',
            hovertemplate='CFOP %{y}<br>Valor: R$ %{x:,.2f}<extra></extra>'
        )
        
        fig.update_layout(
            height=500,
            xaxis_title='Valor (R$)',
            yaxis_title='CFOP',
            xaxis=dict(tickformat=',.2f')
        )
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Erro ao processar CFOPs: {str(e)}",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Distribuição por CFOP')
        return fig