import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import locale

# 1. Configuração de Localidade (Português Brasil)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        st.warning("Não foi possível carregar o locale pt_BR. As datas podem aparecer em inglês.")

# 2. Configuração de Estilo Premium
st.set_page_config(page_title="FASICLIN - Gestão Premium", layout="wide")

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

    /* Estilização do Selectbox (Cinza arredondado) */
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
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Conexão com a Planilha
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
        st.image(LOGO_URL, width=200)
    with col_info:
        st.caption(f"Sincronizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # --- FILTROS (Novo Formato) ---
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    
    # Campo Procedimento
    c_label, c_select = st.columns([0.2, 0.8])
    with c_label:
        st.markdown("<p style='margin-top:10px; font-weight:bold;'>🎯 Procedimento:</p>", unsafe_allow_html=True)
    with c_select:
        procs = ["-- Todos os Procedimentos --"] + sorted(df['PROCEDIMENTO'].dropna().unique().tolist())
        proc_sel = st.selectbox("Procedimento", procs, label_visibility="collapsed")
    
    st.markdown("<hr style='margin: 15px 0; opacity: 0.1;'>", unsafe_allow_html=True)

    # Filtro de Meses (Pílulas com Locale aplicado)
    if 'DATA' in df.columns:
        df['MES_ANO'] = df['DATA'].dt.strftime('%B de %Y')
        meses_unicos = sorted(df['MES_ANO'].dropna().unique().tolist(), key=lambda x: datetime.strptime(x, '%B de %Y'))
        
        cols_mes = st.columns(len(meses_unicos) + 1)
        mes_sel = "Todos os Meses"
        
        if cols_mes[0].button("Todos os Meses", key="btn_todos"):
            mes_sel = "Todos os Meses"
        
        for i, mes in enumerate(meses_unicos):
            if cols_mes[i+1].button(mes.capitalize(), key=f"btn_{i}"):
                mes_sel = mes

        # Aplicando filtros ao DF
        if mes_sel != "Todos os Meses":
            df = df[df['MES_ANO'] == mes_sel]
    
    if proc_sel != "-- Todos os Procedimentos --":
        df = df[df['PROCEDIMENTO'] == proc_sel]

    st.markdown('</div>', unsafe_allow_html=True)

    # --- INDICADORES ---
    t_qtd = df['QUANTIDADE'].sum() if 'QUANTIDADE' in df.columns else 0
    t_finan = df[col_finan].sum()
    dias_ativos = df['DATA'].nunique() if 'DATA' in df.columns else 1
    eficiencia = (t_qtd / (dias_ativos * 40)) if dias_ativos > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Atendimentos", f"{int(t_qtd)}")
    m2.metric("Faturamento Bruto", f"R$ {t_finan:,.2f}")
    m3.metric("Eficiência (Meta 40)", f"{eficiencia:.1%}")

    st.divider()

    # --- GRÁFICO TENDÊNCIA (Estilo Novo) ---
    st.subheader("📈 Tendência de Atingimento de Meta Diária")
    if 'DATA' in df.columns:
        df_meta = df.groupby('DATA')['QUANTIDADE'].sum().reset_index().sort_values('DATA')
        
        fig_meta = go.Figure()

        # Realizado
        fig_meta.add_trace(go.Scatter(
            x=df_meta['DATA'], 
            y=df_meta['QUANTIDADE'], 
            name='Realizado',
            line=dict(color='#299947', width=4, shape='spline'), # Linha curva
            fill='tozeroy',
            fillcolor='rgba(41, 153, 71, 0.1)',
            mode='lines+markers',
            marker=dict(size=8, color='white', line=dict(color='#299947', width=2))
        ))

        # Meta
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
        st.plotly_chart(fig_meta, use_container_width=True)

    # --- OUTROS GRÁFICOS ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🎓 Produção por Turma")
        fig_turma = px.pie(df, values='QUANTIDADE', names='TURMA', hole=0.4, color_discrete_sequence=['#299947', '#a395a8', '#10b981'])
        st.plotly_chart(fig_turma, use_container_width=True)
    with c2:
        st.subheader("🏢 Distribuição por Clínica")
        fig_cli = px.bar(df.groupby('CLINICA')['QUANTIDADE'].sum().reset_index(), x='CLINICA', y='QUANTIDADE', color_discrete_sequence=['#299947'])
        st.plotly_chart(fig_cli, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
