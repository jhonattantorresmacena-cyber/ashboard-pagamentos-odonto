import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuração de Estilo Premium
st.set_page_config(page_title="FASICLIN - Gestão Premium", layout="wide")

# Dicionário para tradução manual dos meses
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

    /* Estilização do Selectbox */
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
    
    /* Botões de Mês (Alinhados à esquerda) */
    .stButton > button {
        border-radius: 20px;
        border: 1px solid #eaeaea;
        background-color: white;
        color: #5f6368;
        padding: 5px 20px;
        width: auto; /* Ajustado para não ocupar a coluna toda */
        min-width: 150px;
    }
    .stButton > button:hover {
        border-color: #299947;
        color: #299947;
    }
    /* Estilo do botão selecionado (Simulação manual via CSS se necessário) */
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
        df[col_finan] = df[col_finan].astype(str).replace(r'[R\$\.\,]', '', regex=True)
        df[col_finan] = pd.to_numeric(df[col_finan], errors='coerce').fillna(0) / 100 [cite: 3]
    return df, col_finan

try:
    df, col_finan = load_data()

    # --- HEADER ---
    LOGO_URL = "https://raw.githubusercontent.com/jhonattantorresmacena-cyber/dashboard-fasiclin/main/assets/image_1.png"
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        st.image(LOGO_URL, width=200)
    with col_info:
        st.caption(f"Sincronizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}") [cite: 4]

    # --- FILTROS (Alinhamento Conforme Referência) ---
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    
    c_label, c_select = st.columns([0.15, 0.85])
    with c_label:
        st.markdown("<p style='margin-top:10px; font-weight:bold;'>🎯 Procedimento:</p>", unsafe_allow_html=True)
    with c_select:
        procs = ["-- Todos os Procedimentos --"] + sorted(df['PROCEDIMENTO'].dropna().unique().tolist())
        proc_sel = st.selectbox("Procedimento", procs, label_visibility="collapsed")
    
    st.markdown("<hr style='margin: 15px 0; opacity: 0.1;'>", unsafe_allow_html=True)

    # Seleção de Datas alinhada à esquerda
    if 'DATA' in df.columns:
        df['MES_NOME_EN'] = df['DATA'].dt.strftime('%B')
        df['MES_TRADUZIDO'] = df['MES_NOME_EN'].map(MESES_TRADUCAO)
        df['MES_ANO'] = df['MES_TRADUZIDO'] + " de " + df['DATA'].dt.strftime('%Y')
        
        meses_lista = df[['MES_ANO', 'DATA']].dropna().sort_values('DATA')['MES_ANO'].unique().tolist()
        
        # Container de botões alinhados à esquerda (usando colunas pequenas)
        cols_btns = st.columns([0.15, 0.15, 0.15, 0.55]) 
        
        if "mes_selecionado" not in st.session_state:
            st.session_state.mes_selecionado = "Todos os Meses"

        with cols_btns[0]:
            if st.button("Todos os Meses", key="btn_all"):
                st.session_state.mes_selecionado = "Todos os Meses"
        
        for i, mes in enumerate(meses_lista[:2]): # Exibindo os 2 meses da imagem
            with cols_btns[i+1]:
                if st.button(mes, key=f"btn_{i}"):
                    st.session_state.mes_selecionado = mes

        if st.session_state.mes_selecionado != "Todos os Meses":
            df = df[df['MES_ANO'] == st.session_state.mes_selecionado]
    
    if proc_sel != "-- Todos os Procedimentos --":
        df = df[df['PROCEDIMENTO'] == proc_sel] [cite: 5]

    st.markdown('</div>', unsafe_allow_html=True)

    # --- INDICADORES ---
    t_qtd = df['QUANTIDADE'].sum() if 'QUANTIDADE' in df.columns else 0
    t_finan = df[col_finan].sum()
    dias_ativos = df['DATA'].nunique() if 'DATA' in df.columns else 1
    eficiencia = (t_qtd / (dias_ativos * 40)) if dias_ativos > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Atendimentos", f"{int(t_qtd)}") [cite: 6]
    m2.metric("Faturamento Bruto", f"R$ {t_finan:,.2f}") [cite: 6]
    m3.metric("Eficiência (Meta 40)", f"{eficiencia:.1%}") [cite: 6]

    st.divider()

    # --- GRÁFICO TENDÊNCIA ---
    st.subheader("📈 Tendência de Atingimento de Meta Diária")
    if 'DATA' in df.columns:
        df_meta = df.groupby('DATA')['QUANTIDADE'].sum().reset_index().sort_values('DATA')
        fig_meta = go.Figure()
        fig_meta.add_trace(go.Scatter(
            x=df_meta['DATA'], y=df_meta['QUANTIDADE'], name='Realizado',
            line=dict(color='#299947', width=4, shape='spline'),
            fill='tozeroy', fillcolor='rgba(41, 153, 71, 0.1)', mode='lines+markers',
            marker=dict(size=8, color='white', line=dict(color='#299947', width=2))
        ))
        fig_meta.add_trace(go.Scatter(
            x=df_meta['DATA'], y=[40]*len(df_meta), name='Meta', 
            line=dict(color='#ff4d4d', width=2, dash='dash')
        ))
        fig_meta.update_layout(
            height=400, hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            xaxis=dict(showgrid=False, tickformat="%d/%m/%Y"), yaxis=dict(showgrid=True, gridcolor='#eaeaea')
        )
        st.plotly_chart(fig_meta, use_container_width=True) [cite: 7]

    # --- NOVOS GRÁFICOS (PIZZA/ROSCA E RANKING) ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🎓 Produção por Turma")
        # Gráfico de Pizza conforme imagem_b15f00.png
        fig_turma = px.pie(df, values='QUANTIDADE', names='TURMA', 
                           color_discrete_sequence=['#299947', '#a395a8'])
        fig_turma.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_turma, use_container_width=True)

    with c2:
        st.subheader("🏢 Distribuição por Clínica")
        # Gráfico de Rosca conforme imagem_b15f00.png
        fig_cli = px.pie(df, values='QUANTIDADE', names='CLINICA', hole=0.6,
                         color_discrete_sequence=['#10b981', '#5f6368', '#f59e0b', '#ef4444'])
        fig_cli.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_cli, use_container_width=True)

    st.markdown("---")
    
    # Ranking de Receita por Procedimento (imagem_b1bc79.png)
    st.subheader("📊 Ranking de Receita por Procedimento")
    df_ranking = df.groupby('PROCEDIMENTO').agg({col_finan: 'sum', 'QUANTIDADE': 'sum'}).reset_index()
    df_ranking = df_ranking.sort_values(col_finan, ascending=True)
    
    fig_rank = px.bar(df_ranking, y='PROCEDIMENTO', x=col_finan, orientation='h',
                      text='QUANTIDADE', color_discrete_sequence=['#299947'])
    
    fig_rank.update_traces(texttemplate='Qtd: %{text}', textposition='outside')
    fig_rank.update_layout(
        xaxis_title="Valor Total (R$)", yaxis_title=None,
        paper_bgcolor='white', plot_bgcolor='white', height=500,
        margin=dict(l=200) # Espaço para nomes longos de procedimentos
    )
    st.plotly_chart(fig_rank, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
