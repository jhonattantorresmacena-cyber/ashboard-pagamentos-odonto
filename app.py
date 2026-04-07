import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuração de Estilo Premium (Cores FASICLIN)
st.set_page_config(page_title="FASICLIN - Gestão Premium", layout="wide")

# Estilização CSS Avançada
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Estilização dos Cards de Métrica */
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        border: 1px solid #efefef;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #299947;
        box-shadow: 0 8px 20px rgba(41, 153, 71, 0.15);
    }

    div[data-testid="stMetricValue"] > div { color: #299947 !important; font-weight: 700; }
    div[data-testid="stMetricLabel"] > div { color: #6c757d !important; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px; }
    
    /* Ajuste de botões */
    .stDownloadButton button {
        width: 100%;
        border-radius: 8px;
        background-color: #299947;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão com a Planilha
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M2TGuEkzyOXgcxGK9ujYDknIgjvWlveHHsSpqnvv5j4/export?format=csv&gid=1575732509"

@st.cache_data(ttl=60) # Aumentado para 60s para estabilidade, ajuste se precisar de mais tempo real
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip().upper() for c in df.columns]
        
        if 'DATA' in df.columns:
            df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['DATA']) # Remove linhas sem data
            df = df.sort_values('DATA') # Ordenação cronológica fundamental
            df['MES_ANO'] = df['DATA'].dt.strftime('%m/%Y - %B') # Formato para ordenação correta
            
        col_finan = 'VALOR TOTAL' if 'VALOR TOTAL' in df.columns else 'VALOR'
        if col_finan in df.columns:
            # Limpeza de strings financeiras
            df[col_finan] = df[col_finan].astype(str).replace(r'[R\$\.\,]', '', regex=True)
            df[col_finan] = pd.to_numeric(df[col_finan], errors='coerce').fillna(0) / 100
        
        return df, col_finan
    except Exception as e:
        st.error(f"Erro na leitura dos dados: {e}")
        return pd.DataFrame(), None

df_raw, col_finan = load_data()

if not df_raw.empty:
    df = df_raw.copy()

    # --- HEADER COM LOGO ---
    LOGO_URL = "https://raw.githubusercontent.com/jhonattantorresmacena-cyber/dashboard-fasiclin/main/assets/image_1.png"
    
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        st.image(LOGO_URL, width=180)
    with col_info:
        st.title("Sistema de Inteligência Clínica")
        st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # --- SIDEBAR (Filtros) ---
    st.sidebar.header("🎯 Filtros de Gestão")
    
    # Filtro de Período (Ordenado)
    meses = ["Todos os Meses"] + df['MES_ANO'].unique().tolist()
    mes_sel = st.sidebar.selectbox("Selecionar Mês", meses)
    if mes_sel != "Todos os Meses":
        df = df[df['MES_ANO'] == mes_sel]

    # Filtro de Procedimento
    procs = ["Todos os Procedimentos"] + sorted(df['PROCEDIMENTO'].dropna().unique().tolist())
    proc_sel = st.sidebar.selectbox("Filtrar Procedimento", procs)
    if proc_sel != "Todos os Procedimentos":
        df = df[df['PROCEDIMENTO'] == proc_sel]

    # Botão de Exportação na Sidebar
    st.sidebar.divider()
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Exportar Dados para Excel/CSV",
        data=csv,
        file_name=f'relatorio_fasiclin_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )

    # --- INDICADORES (KPIs) ---
    t_qtd = df['QUANTIDADE'].sum() if 'QUANTIDADE' in df.columns else 0
    t_finan = df[col_finan].sum()
    dias_ativos = df['DATA'].nunique() if 'DATA' in df.columns else 1
    eficiencia = (t_qtd / (dias_ativos * 40)) if dias_ativos > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Atendimentos", f"{int(t_qtd)}")
    m2.metric("Faturamento", f"R$ {t_finan:,.2f}")
    m3.metric("Eficiência Operacional", f"{eficiencia:.1%}")
    m4.metric("Ticket Médio", f"R$ {(t_finan/t_qtd if t_qtd > 0 else 0):,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    
    # 1. Gráfico de Tendência (Principal)
    st.subheader("📈 Meta Diária vs. Realizado")
    df_meta = df.groupby('DATA')['QUANTIDADE'].sum().reset_index()
    fig_meta = go.Figure()
    fig_meta.add_trace(go.Scatter(
        x=df_meta['DATA'], y=df_meta['QUANTIDADE'], 
        name='Atendimentos Realizados', 
        line=dict(color='#299947', width=4),
        fill='tozeroy', fillcolor='rgba(41, 153, 71, 0.1)'
    ))
    fig_meta.add_trace(go.Scatter(
        x=df_meta['DATA'], y=[40]*len(df_meta), 
        name='Meta (40)', 
        line=dict(color='#ff4d4d', dash='dash', width=2)
    ))
    fig_meta.update_layout(
        height=300, 
        margin=dict(l=0, r=0, t=10, b=0), 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    st.plotly_chart(fig_meta, use_container_width=True)

    # 2. Distribuição por Clínica e Turma
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🎓 Produção por Turma")
        fig_turma = px.pie(df, values='QUANTIDADE', names='TURMA', hole=0.5, 
                           color_discrete_sequence=px.colors.sequential.Greens_r)
        fig_turma.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_turma, use_container_width=True)
    with c2:
        st.subheader("🏢 Volume por Clínica")
        df_cli = df.groupby('CLINICA')['QUANTIDADE'].sum().sort_values(ascending=True).reset_index()
        fig_cli = px.bar(df_cli, x='QUANTIDADE', y='CLINICA', orientation='h',
                         color_discrete_sequence=['#299947'])
        fig_cli.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_cli, use_container_width=True)

    # 3. Ranking de Procedimentos (Nova Visão)
    st.divider()
    st.subheader("📋 Top Procedimentos Realizados")
    df_proc = df.groupby('PROCEDIMENTO')['QUANTIDADE'].sum().sort_values(ascending=False).head(10).reset_index()
    fig_proc = px.bar(df_proc, x='PROCEDIMENTO', y='QUANTIDADE', 
                      color='QUANTIDADE', color_continuous_scale='Greens')
    st.plotly_chart(fig_proc, use_container_width=True)

else:
    st.error("Não foi possível carregar os dados. Verifique a conexão com a planilha.")
