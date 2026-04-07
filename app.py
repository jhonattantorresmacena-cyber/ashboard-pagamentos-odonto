import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import locale

# Tenta configurar o locale para Português (Brasil) para os nomes dos meses
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.utf8")
except:
    try:
        locale.setlocale(locale.LC_TIME, "Portuguese_Brazil.1252")
    except:
        pass # Caso o servidor não tenha o locale instalado

# 1. Configuração de Estilo e Metas
st.set_page_config(page_title="FASICLIN - Gestão Premium", layout="wide")

# DEFINA AQUI AS METAS POR CLÍNICA
METAS_CLINICAS = {
    "CLINICA A": 50,
    "CLINICA B": 30,
    "GERAL": 40  # Meta padrão caso a clínica não esteja na lista
}

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        border-left: 5px solid #299947;
    }
    /* Estilo para as métricas dinâmicas */
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
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
        df = df.dropna(subset=['DATA']).sort_values('DATA')
        # Mês em Português sem o ano
        df['MES_NOME'] = df['DATA'].dt.strftime('%B').str.capitalize()
    
    col_finan = 'VALOR TOTAL' if 'VALOR TOTAL' in df.columns else 'VALOR'
    if col_finan in df.columns:
        df[col_finan] = df[col_finan].astype(str).replace(r'[R\$\.\,]', '', regex=True)
        df[col_finan] = pd.to_numeric(df[col_finan], errors='coerce').fillna(0) / 100
    return df, col_finan

df_raw, col_finan = load_data()

if not df_raw.empty:
    df = df_raw.copy()

    # --- CABEÇALHO (Apenas Logo) ---
    LOGO_URL = "https://raw.githubusercontent.com/jhonattantorresmacena-cyber/dashboard-fasiclin/main/assets/image_1.png"
    st.image(LOGO_URL, width=220)
    st.caption(f"Sincronizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # --- SIDEBAR (Filtros) ---
    st.sidebar.header("🎯 Filtros")
    
    # Filtro Mês em PT-BR
    meses_disponiveis = ["Todos os Meses"] + list(df['MES_NOME'].unique())
    mes_sel = st.sidebar.selectbox("Selecionar Mês", meses_disponiveis)
    if mes_sel != "Todos os Meses":
        df = df[df['MES_NOME'] == mes_sel]

    # Filtro Clínica (Para Meta Dinâmica)
    clinicas = ["Todas as Clínicas"] + sorted(df['CLINICA'].unique().tolist())
    clinica_sel = st.sidebar.selectbox("Selecionar Clínica", clinicas)
    if clinica_sel != "Todas as Clínicas":
        df = df[df['CLINICA'] == clinica_sel]
        meta_atual = METAS_CLINICAS.get(clinica_sel, METAS_CLINICAS["GERAL"])
    else:
        meta_atual = METAS_CLINICAS["GERAL"]

    # --- CÁLCULOS ---
    t_qtd = df['QUANTIDADE'].sum()
    t_finan = df[col_finan].sum()
    dias_ativos = df['DATA'].nunique()
    eficiencia = (t_qtd / (dias_ativos * meta_atual)) if dias_ativos > 0 else 0

    # Definição de Cores para Alertas
    cor_eficiencia = "#299947" if eficiencia >= 0.8 else "#f1c40f" if eficiencia >= 0.5 else "#e74c3c"

    # --- KPIs ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Atendimentos Total", f"{int(t_qtd)}")
    m2.metric("Faturamento", f"R$ {t_finan:,.2f}")
    
    # Métrica de Eficiência com cor dinâmica via Markdown (Hack de Estilo)
    with m3:
        st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 15px; border-left: 5px solid {cor_eficiencia}; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <p style="color: #6c757d; margin:0; font-size: 0.85rem; text-transform: uppercase;">Eficiência (Meta: {meta_atual})</p>
                <h2 style="color: {cor_eficiencia}; margin:0;">{eficiencia:.1%}</h2>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- GRÁFICO DE TENDÊNCIA REFINADO ---
    st.subheader("📈 Meta Diária vs. Realizado")
    df_meta = df.groupby('DATA')['QUANTIDADE'].sum().reset_index()
    
    fig_meta = go.Figure()

    # Linha do Realizado (Curva Suavizada e Pontos Destacados)
    fig_meta.add_trace(go.Scatter(
        x=df_meta['DATA'], 
        y=df_meta['QUANTIDADE'], 
        name='Realizado',
        mode='lines+markers', # Adiciona os pontos
        line=dict(color='#299947', width=4, shape='spline'), # 'spline' cria a curva acentuada
        marker=dict(size=10, color='#1e3d24', symbol='circle', line=dict(width=2, color='white')), # Destaque nos pontos
        fill='tozeroy', 
        fillcolor='rgba(41, 153, 71, 0.1)'
    ))

    # Linha da Meta
    fig_meta.add_trace(go.Scatter(
        x=df_meta['DATA'], 
        y=[meta_atual]*len(df_meta), 
        name=f'Meta ({meta_atual})', 
        line=dict(color='#e74c3c', dash='dash', width=2)
    ))

    fig_meta.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=10, b=0),
        hovermode="x unified",
        xaxis=dict(
            tickformat="%d/%m", # Data abreviada como na planilha (ex: 07/04)
            showgrid=False,
            tickfont=dict(color='#6c757d')
        ),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_meta, use_container_width=True)

    # --- DEMAIS GRÁFICOS ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🎓 Produção por Turma")
        fig_turma = px.pie(df, values='QUANTIDADE', names='TURMA', hole=0.5,
                           color_discrete_sequence=px.colors.sequential.Greens_r)
        st.plotly_chart(fig_turma, use_container_width=True)
    with c2:
        st.subheader("🏢 Volume por Clínica")
        df_cli = df.groupby('CLINICA')['QUANTIDADE'].sum().sort_values(ascending=True).reset_index()
        fig_cli = px.bar(df_cli, x='QUANTIDADE', y='CLINICA', orientation='h', color_discrete_sequence=['#299947'])
        st.plotly_chart(fig_cli, use_container_width=True)

else:
    st.error("Dados não encontrados. Verifique a planilha.")
