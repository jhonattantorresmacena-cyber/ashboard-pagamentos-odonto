import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Configuração de Estilo e Layout
st.set_page_config(page_title="FASICLIN - Gestão Executiva", layout="wide")

MESES_TRADUCAO = {
    'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
    'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
    'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
    'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
}

st.markdown("""
    <style>
    .main { background-color: #f0f2f5; }
    .filter-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #eaeaea;
    }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; padding: 20px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #eaeaea; 
    }
    /* Estilo para Alertas de Meta */
    .status-bom { color: #299947; font-weight: bold; }
    .status-alerta { color: #f59e0b; font-weight: bold; }
    .status-critico { color: #ef4444; font-weight: bold; }
    
    .stButton > button { border-radius: 20px; min-width: 120px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carregamento de Dados
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M2TGuEkzyOXgcxGK9ujYDknIgjvWlveHHsSpqnvv5j4/export?format=csv&gid=1575732509"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [c.strip().upper() for c in df.columns]
    if 'DATA' in df.columns:
        df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
    
    col_finan = 'VALOR TOTAL' if 'VALOR TOTAL' in df.columns else 'VALOR'
    if col_finan in df.columns:
        df[col_finan] = df[col_finan].astype(str).replace(r'[R\$\.\,]', '', regex=True)
        df[col_finan] = pd.to_numeric(df[col_finan], errors='coerce').fillna(0) / 100
    return df, col_finan

try:
    df_raw, col_finan = load_data()
    df = df_raw.copy()

    # --- HEADER & BOTÃO ATUALIZAR ---
    col_logo, col_refresh = st.columns([4, 1])
    with col_logo:
        st.image("https://raw.githubusercontent.com/jhonattantorresmacena-cyber/dashboard-fasiclin/main/assets/image_1.png", width=180)
    with col_refresh:
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()

    # --- FILTROS INTELIGENTES ---
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 2])
    
    with c1:
        start_date = st.date_input("Início", df['DATA'].min())
    with c2:
        end_date = st.date_input("Fim", df['DATA'].max())
    with c3:
        procs = ["-- Todos os Procedimentos --"] + sorted(df['PROCEDIMENTO'].dropna().unique().tolist())
        proc_sel = st.selectbox("🎯 Filtrar Procedimento", procs)

    # Aplicação dos Filtros
    df = df[(df['DATA'] >= pd.to_datetime(start_date)) & (df['DATA'] <= pd.to_datetime(end_date))]
    if proc_sel != "-- Todos os Procedimentos --":
        df = df[df['PROCEDIMENTO'] == proc_sel]
    st.markdown('</div>', unsafe_allow_html=True)

    # --- CÁLCULOS DE GESTÃO AVANÇADA ---
    t_qtd = df['QUANTIDADE'].sum()
    t_finan = df[col_finan].sum()
    ticket_medio = t_finan / t_qtd if t_qtd > 0 else 0
    
    # Projeção de Fechamento (Baseado na média diária do período filtrado)
    dias_periodo = (df['DATA'].max() - df['DATA'].min()).days + 1
    media_diaria = t_qtd / dias_periodo if dias_periodo > 0 else 0
    projecao_30d = media_diaria * 30

    # Lógica de Alerta de Meta (Baseado em Eficiência de 40 atendimentos/dia)
    eficiencia = (media_diaria / 40) if media_diaria > 0 else 0
    if eficiencia >= 0.9:
        status_classe = "status-bom"
        status_texto = "🎯 META ATINGIDA"
    elif eficiencia >= 0.7:
        status_classe = "status-alerta"
        status_texto = "⚠️ ATENÇÃO: ABAIXO DA META"
    else:
        status_classe = "status-critico"
        status_texto = "🚨 CRÍTICO: REVISAR OPERAÇÃO"

    # --- INDICADORES (Cards Profissionais) ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Faturamento Total", f"R$ {t_finan:,.2f}")
    m2.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
    m3.metric("Eficiência Atual", f"{eficiencia:.1%}")
    with m4:
        st.markdown(f"**Status da Meta**")
        st.markdown(f'<p class="{status_classe}">{status_texto}</p>', unsafe_allow_html=True)
        st.caption(f"Projeção 30 dias: {int(projecao_30d)} atend.")

    st.divider()

    # --- BENCHMARK ENTRE TURMAS (Gráfico de Radar) ---
    st.subheader("📊 Benchmark: Performance por Turma")
    turmas_data = df.groupby('TURMA').agg({
        'QUANTIDADE': 'sum',
        col_finan: 'sum',
        'PROCEDIMENTO': 'nunique'
    }).reset_index()

    if not turmas_data.empty:
        fig_radar = go.Figure()
        for i, row in turmas_data.iterrows():
            fig_radar.add_trace(go.Scatterpolar(
                r=[row['QUANTIDADE'], row[col_finan]/100, row['PROCEDIMENTO']*10], # Normalização simples para escala
                theta=['Volume','Receita (x100)','Variedade'],
                fill='toself', name=f"Turma {row['TURMA']}"
            ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=400)
        st.plotly_chart(fig_radar, use_container_width=True)

    # --- PARETO DE RECEITA & HEATMAP ---
    c_p1, c_p2 = st.columns(2)
    
    with c_p1:
        st.subheader("🥇 Curva ABC (Pareto de Receita)")
        df_pareto = df.groupby('PROCEDIMENTO')[col_finan].sum().sort_values(ascending=False).reset_index()
        df_pareto['Acumulado'] = df_pareto[col_finan].cumsum() / df_pareto[col_finan].sum() * 100
        fig_pareto = px.bar(df_pareto, x='PROCEDIMENTO', y=col_finan, color_discrete_sequence=['#299947'])
        fig_pareto.add_scatter(x=df_pareto['PROCEDIMENTO'], y=df_pareto['Acumulado'], name='% Acumulada', yaxis='y2', line=dict(color='#ef4444'))
        fig_pareto.update_layout(yaxis2=dict(overlaying='y', side='right', range=[0, 100]), showlegend=False)
        st.plotly_chart(fig_pareto, use_container_width=True)

    with c_p2:
        st.subheader("📅 Heatmap: Volume por Dia da Semana")
        df['DIA_SEMANA'] = df['DATA'].dt.day_name().map({'Monday':'Seg', 'Tuesday':'Ter', 'Wednesday':'Qua', 'Thursday':'Qui', 'Friday':'Sex', 'Saturday':'Sab'})
        heat_data = df.groupby('DIA_SEMANA')['QUANTIDADE'].sum().reindex(['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']).reset_index()
        fig_heat = px.density_heatmap(heat_data, x='DIA_SEMANA', y='QUANTIDADE', color_continuous_scale='Greens')
        st.plotly_chart(fig_heat, use_container_width=True)

    # --- TABELA DE DETALHES (Drill-down) ---
    with st.expander("🔍 Detalhamento dos Dados e Exportação"):
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Relatório CSV", data=csv, file_name="relatorio_fasiclin.csv", mime="text/csv")

except Exception as e:
    st.error(f"Erro na análise: {e}")
