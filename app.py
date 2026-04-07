import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuração de Estilo "Premium" (Inspirado no seu HTML)
st.set_page_config(page_title="FASICLIN - Gestão Premium", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f5; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #eaeaea; }
    .stMetric div[data-testid="stMetricValue"] { color: #299947; font-weight: 600; }
    .stMetric div[data-testid="stMetricLabel"] { color: #a395a8; text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem; }
    h1, h2, h3 { font-family: 'Poppins', sans-serif; color: #333333; }
    div[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    </style>
    """, unsafe_allow_cases=True)

# 2. Conexão com os Dados
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M2TGuEkzyOXgcxGK9ujYDknIgjvWlveHHsSpqnvv5j4/export?format=csv&gid=1575732509"

@st.cache_data(ttl=5)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [c.strip().upper() for c in df.columns]
    
    # Tratamento de Datas
    if 'DATA' in df.columns:
        df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
    
    # Tratamento de Valores Financeiros
    col_valor = 'VALOR TOTAL' if 'VALOR TOTAL' in df.columns else 'VALOR'
    if col_valor in df.columns:
        df[col_valor] = df[col_valor].replace(r'[R\$\.\,]', '', regex=True).fillna(0)
        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce') / 100
        
    return df, col_valor

try:
    df, col_finan = load_data()

    # --- SIDEBAR (Filtros Estilo HTML) ---
    st.sidebar.header("🎯 Filtros de Gestão")
    
    # Filtro de Mês (Igual aos botões do seu HTML)
    if 'DATA' in df.columns:
        df['MES_ANO'] = df['DATA'].dt.strftime('%B %Y')
        meses = ["Todos os Meses"] + sorted(df['MES_ANO'].dropna().unique().tolist())
        mes_sel = st.sidebar.selectbox("Selecionar Período", meses)
        if mes_sel != "Todos os Meses":
            df = df[df['MES_ANO'] == mes_sel]

    # Filtro de Procedimento
    procs = ["Todos os Procedimentos"] + sorted(df['PROCEDIMENTO'].dropna().unique().tolist())
    proc_sel = st.sidebar.selectbox("Procedimento", procs)
    if proc_sel != "Todos os Procedimentos":
        df = df[df['PROCEDIMENTO'] == proc_sel]

    # --- HEADER ---
    st.title("🏥 FASICLIN - Gestão Premium")
    st.markdown(f"**Sincronização Ativa:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # --- INDICADORES (Cards do seu HTML) ---
    t_qtd = df['QUANTIDADE'].sum() if 'QUANTIDADE' in df.columns else 0
    t_finan = df[col_finan].sum()
    # Cálculo de eficiência baseado na meta de 40 do seu HTML
    dias_ativos = df['DATA'].nunique() if 'DATA' in df.columns else 1
    eficiencia = (t_qtd / (dias_ativos * 40)) if dias_ativos > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Atendimentos", f"{int(t_qtd):,}".replace(',', '.'))
    m2.metric("Faturamento Bruto", f"R$ {t_finan:,.2f}")
    m3.metric("Eficiência Média (Meta 40)", f"{eficiencia:.1%}")

    st.divider()

    # --- GRÁFICOS ---
    
    # 1. Tendência de Atingimento de Meta (Gráfico de Linha)
    st.subheader("📈 Tendência de Atingimento de Meta Diária")
    if 'DATA' in df.columns:
        df_meta = df.groupby('DATA')['QUANTIDADE'].sum().reset_index()
        fig_meta = go.Figure()
        fig_meta.add_trace(go.Scatter(x=df_meta['DATA'], y=df_meta['QUANTIDADE'], name='Realizado', line=dict(color='#299947', width=3), fill='tozeroy'))
        fig_meta.add_trace(go.Scatter(x=df_meta['DATA'], y=[40]*len(df_meta), name='Meta Diária', line=dict(color='#ff4d4d', dash='dash')))
        fig_meta.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_meta, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🎓 Produção por Turma")
        fig_turma = px.pie(df, values='QUANTIDADE', names='TURMA', hole=0.4, color_discrete_sequence=['#299947', '#a395a8', '#34d399'])
        st.plotly_chart(fig_turma, use_container_width=True)

    with c2:
        st.subheader("🏢 Distribuição por Clínica")
        fig_cli = px.bar(df.groupby('CLINICA')['QUANTIDADE'].sum().reset_index(), x='CLINICA', y='QUANTIDADE', color='CLINICA', color_discrete_sequence=['#10b981', '#6b7280'])
        st.plotly_chart(fig_cli, use_container_width=True)

    # 2. Ranking de Receita (Igual ao seu HTML)
    st.subheader("🏆 Ranking de Receita por Procedimento")
    df_rank = df.groupby('PROCEDIMENTO')[col_finan].sum().sort_values(ascending=True).reset_index()
    fig_rank = px.bar(df_rank, x=col_finan, y='PROCEDIMENTO', orientation='h', color_discrete_sequence=['#299947'])
    fig_rank.update_layout(height=500)
    st.plotly_chart(fig_rank, use_container_width=True)

    # Tabela de Dados
    with st.expander("📄 Visualizar Dados Detalhados"):
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Erro na renderização: {e}")
