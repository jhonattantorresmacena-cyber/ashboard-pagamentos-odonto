import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# 1. Configuração de Estilo e Layout
st.set_page_config(page_title="FASICLIN - Gestão Premium", layout="wide")

# Dicionário de tradução para meses
MESES_TRADUCAO = {
    'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
    'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
    'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
    'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
}

# Estilização CSS personalizada
st.markdown("""
    <style>
    .main { background-color: #f0f2f5; }
    .filter-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #eaeaea;
    }
    div[data-baseweb="select"] > div {
        background-color: #f1f3f4 !important;
        border-radius: 25px !important;
        border: none !important;
    }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); 
        border: 1px solid #eaeaea; 
    }
    div[data-testid="stMetricValue"] > div { color: #299947 !important; font-weight: 600; }
    div[data-testid="stMetricLabel"] > div { color: #a395a8 !important; text-transform: uppercase; font-size: 0.8rem; }
    
    .stButton > button {
        border-radius: 20px;
        transition: all 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Carregamento de Dados
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M2TGuEkzyOXgcxGK9ujYDknIgjvWlveHHsSpqnvv5j4/export?format=csv&gid=1575732509"

@st.cache_data(ttl=60) # Aumentado para 60s para estabilidade, ajuste conforme necessário
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
    df, col_finan = load_data()

    # --- CABEÇALHO ---
    col_logo, col_vazio, col_info = st.columns([1, 2, 1.5])
    with col_logo:
        LOGO_URL = "https://raw.githubusercontent.com/jhonattantorresmacena-cyber/dashboard-fasiclin/main/assets/image_1.png"
        st.image(LOGO_URL, width=180)
    with col_info:
        st.markdown(f"""
            <div style='text-align: right; color: #a395a8; font-size: 0.9rem; margin-top: 15px;'>
                <b>Sincronizado em:</b><br>{datetime.now().strftime('%d/%m/%Y às %H:%M')}
            </div>
            """, unsafe_allow_html=True)

    # --- FILTROS ---
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    c_label, c_select = st.columns([0.15, 0.85])
    with c_label:
        st.markdown("<p style='margin-top:10px; font-weight:bold;'>🎯 Procedimento:</p>", unsafe_allow_html=True)
    with c_select:
        procs = ["-- Todos os Procedimentos --"] + sorted(df['PROCEDIMENTO'].dropna().unique().tolist())
        proc_sel = st.selectbox("Procedimento", procs, label_visibility="collapsed")
    
    st.markdown("<hr style='margin: 15px 0; opacity: 0.1;'>", unsafe_allow_html=True)

    if 'DATA' in df.columns:
        df['MES_NOME_EN'] = df['DATA'].dt.strftime('%B')
        df['MES_TRADUZIDO'] = df['MES_NOME_EN'].map(MESES_TRADUCAO)
        df['MES_ANO'] = df['MES_TRADUZIDO'] + " de " + df['DATA'].dt.strftime('%Y')
        meses_lista = df[['MES_ANO', 'DATA']].dropna().sort_values('DATA')['MES_ANO'].unique().tolist()
        
        if "mes_selecionado" not in st.session_state:
            st.session_state.mes_selecionado = "Todos os Meses"

        opcoes_mes = ["Todos os Meses"] + meses_lista[:11] # Limite para não quebrar layout
        cols_btns = st.columns(len(opcoes_mes))
        
        for idx, opcao in enumerate(opcoes_mes):
            with cols_btns[idx]:
                is_active = st.session_state.mes_selecionado == opcao
                cor_btn = "#299947" if is_active else "white"
                texto_btn = "white" if is_active else "#5f6368"
                border_btn = "#299947" if is_active else "#eaeaea"
                
                if st.button(opcao, key=f"btn_{opcao}", use_container_width=True):
                    st.session_state.mes_selecionado = opcao
                    st.rerun()
                
                st.markdown(f"""
                    <style>
                    div[data-testid="stHorizontalBlock"] > div:nth-child({idx+1}) button {{
                        background-color: {cor_btn} !important;
                        color: {texto_btn} !important;
                        border-color: {border_btn} !important;
                    }}
                    </style>
                """, unsafe_allow_html=True)

        if st.session_state.mes_selecionado != "Todos os Meses":
            df = df[df['MES_ANO'] == st.session_state.mes_selecionado]
    
    if proc_sel != "-- Todos os Procedimentos --":
        df = df[df['PROCEDIMENTO'] == proc_sel]
    st.markdown('</div>', unsafe_allow_html=True)

    # --- MÉTRICAS ---
    t_qtd = df['QUANTIDADE'].sum() if 'QUANTIDADE' in df.columns else 0
    t_finan = df[col_finan].sum()
    dias_ativos = df['DATA'].nunique() if 'DATA' in df.columns else 1
    
    # Cálculo de Eficiência Refinado
    meta_diaria = 40
    eficiencia = (t_qtd / (dias_ativos * meta_diaria)) if dias_ativos > 0 else 0
    delta_eficiencia = eficiencia - 1.0 # Comparação com 100% da meta

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Atendimentos", f"{int(t_qtd)}")
    m2.metric("Faturamento Bruto", f"R$ {t_finan:,.2f}")
    m3.metric(
        "Eficiência (Meta 40/dia)", 
        f"{eficiencia:.1%}", 
        delta=f"{delta_eficiencia:.1%}",
        delta_color="normal" if eficiencia >= 1 else "inverse"
    )

    st.divider()

    # --- TENDÊNCIA E GRÁFICOS ---
    st.subheader("📈 Tendência de Atingimento de Meta Diária")
    if 'DATA' in df.columns and not df.empty:
        df_meta = df.groupby('DATA')['QUANTIDADE'].sum().reset_index().sort_values('DATA')
        fig_meta = go.Figure()
        fig_meta.add_trace(go.Scatter(
            x=df_meta['DATA'], y=df_meta['QUANTIDADE'], name='Realizado',
            line=dict(color='#299947', width=4, shape='spline'),
            fill='tozeroy', fillcolor='rgba(41, 153, 71, 0.1)', mode='lines+markers',
            marker=dict(size=8, color='white', line=dict(color='#299947', width=2))
        ))
        fig_meta.add_trace(go.Scatter(x=df_meta['DATA'], y=[meta_diaria]*len(df_meta), name='Meta Diária', line=dict(color='#ff4d4d', width=2, dash='dash')))
        fig_meta.update_layout(height=350, hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20))
        st.plotly_chart(fig_meta, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🎓 Produção por Turma")
        if not df.empty:
            fig_turma = px.pie(df, values='QUANTIDADE', names='TURMA', color_discrete_sequence=['#299947', '#a395a8'])
            st.plotly_chart(fig_turma, use_container_width=True)
    with c2:
        st.subheader("🏢 Distribuição por Clínica")
        if not df.empty:
            fig_cli = px.pie(df, values='QUANTIDADE', names='CLINICA', hole=0.6, color_discrete_sequence=['#10b981', '#5f6368', '#f59e0b', '#ef4444'])
            st.plotly_chart(fig_cli, use_container_width=True)

    # --- GRÁFICO DIA DA SEMANA ---
    st.subheader("📅 Produtividade por Dia da Semana")
    if 'DATA' in df.columns and not df.empty:
        df['DIA_SEMANA'] = df['DATA'].dt.day_name().map({
            'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
            'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        })
        ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        df_dia = df.groupby('DIA_SEMANA')['QUANTIDADE'].sum().reindex(ordem_dias).reset_index().fillna(0)
        
        fig_dia = px.bar(df_dia, x='DIA_SEMANA', y='QUANTIDADE', color_discrete_sequence=['#a395a8'], text_auto=True)
        fig_dia.update_traces(textposition='outside', textfont=dict(weight='bold'))
        fig_dia.update_layout(xaxis_title=None, yaxis_title="Qtd Atendimentos", height=350, margin=dict(t=30))
        st.plotly_chart(fig_dia, use_container_width=True)

    # --- NOVO: RANKING DE PROCEDIMENTOS ---
    st.subheader("🏆 Ranking de Procedimentos (Top 10)")
    if not df.empty:
        # Agrupando e pegando os 10 principais
        df_rank = df.groupby('PROCEDIMENTO')['QUANTIDADE'].sum().reset_index()
        df_rank = df_rank.sort_values('QUANTIDADE', ascending=True).tail(10) # Ascending=True para o gráfico de barras horizontais ficar correto
        
        fig_rank = px.bar(
            df_rank, 
            y='PROCEDIMENTO', 
            x='QUANTIDADE', 
            orientation='h',
            color='QUANTIDADE',
            color_continuous_scale='Greens',
            text_auto=True
        )
        
        fig_rank.update_traces(textposition='outside', textfont=dict(weight='bold'))
        fig_rank.update_layout(
            xaxis_title="Quantidade Total",
            yaxis_title=None,
            height=450,
            margin=dict(l=20, r=20, t=20, b=20),
            coloraxis_showscale=False # Esconde a barra de legenda lateral para um visual mais limpo
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    # --- TENDÊNCIA E GRÁFICOS (Restante do código continua abaixo) ---
    st.divider()
    st.subheader("📈 Tendência de Atingimento de Meta Diária")
    # ... o restante do seu código segue aqui ...

    # --- EXPANDER DE EXPORTAÇÃO ---
    with st.expander("🔍 Detalhamento dos Dados e Exportação"):
        df_view = df.copy()
        if 'DATA' in df_view.columns:
            df_view['DATA'] = df_view['DATA'].dt.strftime('%d/%m/%Y')
        
        st.dataframe(df_view, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_view.to_excel(writer, index=False, sheet_name='Relatorio')
        
        st.download_button(
            label="📥 Baixar Relatório Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"relatorio_fasiclin_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

except Exception as e:
    st.error(f"Ocorreu um erro ao processar o dashboard: {e}")
