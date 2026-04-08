import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuração de Estilo Premium
st.set_page_config(page_title="FASICLIN - Gestão Premium", layout="wide")

# Dicionário para tradução manual dos meses (Garante o funcionamento sem erro de locale)
MESES_TRADUCAO = {
    'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
    'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
    'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
    'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
}

st.markdown("""
    <style>
    .main { background-color: #f0f2f5; }
    
    /* Container do Filtro */
    .filter-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #eaeaea;
    }

    /* Estilização do Selectbox (Cinza arredondado igual à imagem) */
    div[data-baseweb="select"] > div {
        background-color: #f1f3f4 !important;
        border-radius: 25px !important;
        border: none !important;
    }

    /* Métricas */
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); 
        border: 1px solid #eaeaea; 
    }
    div[data-testid="stMetricValue"] > div { color: #299947 !important; font-weight: 600; }
    div[data-testid="stMetricLabel"] > div { color: #a395a8 !important; text-transform: uppercase; font-size: 0.8rem; }
    
    /* Botões de Mês (Pílulas) */
    .stButton > button {
        border-radius: 20px;
        border: 1px solid #eaeaea;
        background-color: white;
        color: #5f6368;
        padding: 5px 20px;
        width: 100%;
    }
    .stButton > button:hover {
        border-color: #299947;
        color: #299947;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão com a Planilha
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M2TGuEkzyOXgcxGK9ujYDknIgjvWlveHHsSpqnvv5j4/export?format=csv&gid=1575732509"

@st.cache_data(ttl=5)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [c.strip().upper() for c in df.columns]
    if 'DATA' in df.columns:
        df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
    
    col_finan = 'VALOR TOTAL' if 'VALOR TOTAL' in df.columns else 'VALOR'
    if col_finan in df.columns:
        df[col_finan] = df[col_finan].replace(r'[R\$\.\,]', '', regex=True).fillna(0)
        df[col_finan] = pd.to_numeric(df[col_finan], errors='coerce') / 100
    return df, col_finan

try:
    df, col_finan = load_data()

    # --- HEADER COM LOGO ---
    LOGO_URL = "https://raw.githubusercontent.com/jhonattantorresmacena-cyber/dashboard-fasiclin/main/assets/image_1.png"
    
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        st.image(LOGO_URL, width=200) [cite: 4]
    with col_info:
        st.caption(f"Sincronizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}") [cite: 4]

    # --- FILTROS ---
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    
    # Campo Procedimento
    c_label, c_select = st.columns([0.15, 0.85])
    with c_label:
        st.markdown("<p style='margin-top:10px; font-weight:bold;'>🎯 Procedimento:</p>", unsafe_allow_html=True)
    with c_select:
        procs = ["-- Todos os Procedimentos --"] + sorted(df['PROCEDIMENTO'].dropna().unique().tolist()) [cite: 5]
        proc_sel = st.selectbox("Procedimento", procs, label_visibility="collapsed") [cite: 5]
    
    st.markdown("<hr style='margin: 15px 0; opacity: 0.1;'>", unsafe_allow_html=True)

    # Filtro de Meses (Tradução Manual)
    if 'DATA' in df.columns:
        # Cria nome do mês em inglês e traduz usando o dicionário
        df['MES_NOME_EN'] = df['DATA'].dt.strftime('%B')
        df['MES_TRADUZIDO'] = df['MES_NOME_EN'].map(MESES_TRADUCAO)
        df['MES_ANO'] = df['MES_TRADUZIDO'] + " de " + df['DATA'].dt.strftime('%Y')
        
        meses_unicos = df[['MES_ANO', 'DATA']].dropna().sort_values('DATA')
        meses_lista = meses_unicos['MES_ANO'].unique().tolist()
        
        cols_mes = st.columns(len(meses_lista) + 1)
        
        # Lógica para manter o estado da seleção
        if "mes_selecionado" not in st.session_state:
            st.session_state.mes_selecionado = "Todos os Meses"

        if cols_mes[0].button("Todos os Meses"):
            st.session_state.mes_selecionado = "Todos os Meses"
        
        for i, mes in enumerate(meses_lista):
            if cols_mes[i+1].button(mes):
                st.session_state.mes_selecionado = mes

        # Filtragem Final
        if st.session_state.mes_selecionado != "Todos os Meses":
            df = df[df['MES_ANO'] == st.session_state.mes_selecionado]
    
    if proc_sel != "-- Todos os Procedimentos --":
        df = df[df['PROCEDIMENTO'] == proc_sel] [cite: 5]

    st.markdown('</div>', unsafe_allow_html=True)

    # --- INDICADORES ---
    t_qtd = df['QUANTIDADE'].sum() if 'QUANTIDADE' in df.columns else 0 [cite: 6]
    t_finan = df[col_finan].sum() [cite: 6]
    dias_ativos = df['DATA'].nunique() if 'DATA' in df.columns else 1 [cite: 6]
    eficiencia = (t_qtd / (dias_ativos * 40)) if dias_ativos > 0 else 0 [cite: 6]

    m1, m2, m3 = st.columns(3) [cite: 6]
    m1.metric("Total Atendimentos", f"{int(t_qtd)}") [cite: 6]
    m2.metric("Faturamento Bruto", f"R$ {t_finan:,.2f}") [cite: 6]
    m3.metric("Eficiência (Meta 40)", f"{eficiencia:.1%}") [cite: 6]

    st.divider()

    # --- GRÁFICO TENDÊNCIA ---
    st.subheader("📈 Tendência de Atingimento de Meta Diária") [cite: 7]
    if 'DATA' in df.columns:
        df_meta = df.groupby('DATA')['QUANTIDADE'].sum().reset_index().sort_values('DATA') [cite: 7]
        
        fig_meta = go.Figure()

        # Realizado (Verde com preenchimento)
        fig_meta.add_trace(go.Scatter(
            x=df_meta['DATA'], 
            y=df_meta['QUANTIDADE'], 
            name='Realizado',
            line=dict(color='#299947', width=4, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(41, 153, 71, 0.1)',
            mode='lines+markers',
            marker=dict(size=8, color='white', line=dict(color='#299947', width=2))
        ))

        # Meta (Vermelha Tracejada)
        fig_meta.add_trace(go.Scatter(
            x=df_meta['DATA'], 
            y=[40]*len(df_meta), 
            name='Meta', 
            line=dict(color='#ff4d4d', width=2, dash='dash')
        ))

        fig_meta.update_layout(
            height=400,
            hovermode="x unified",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            xaxis=dict(showgrid=False, tickangle=-45, tickformat="%d/%m/%Y"),
            yaxis=dict(showgrid=True, gridcolor='#eaeaea', range=[0, max(df_meta['QUANTIDADE'].max(), 50) + 10])
        )
        st.plotly_chart(fig_meta, use_container_width=True) [cite: 7]

    # --- OUTROS GRÁFICOS ---
    c1, c2 = st.columns(2) [cite: 8]
    with c1:
        st.subheader("🎓 Produção por Turma") [cite: 8]
        fig_turma = px.pie(df, values='QUANTIDADE', names='TURMA', hole=0.4, color_discrete_sequence=['#299947', '#a395a8', '#10b981']) [cite: 8]
        st.plotly_chart(fig_turma, use_container_width=True) [cite: 8]
    with c2:
        st.subheader("🏢 Distribuição por Clínica") [cite: 8]
        fig_cli = px.bar(df.groupby('CLINICA')['QUANTIDADE'].sum().reset_index(), x='CLINICA', y='QUANTIDADE', color_discrete_sequence=['#299947']) [cite: 8]
        st.plotly_chart(fig_cli, use_container_width=True) [cite: 8]

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
