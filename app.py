import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Fiscalização Odonto", layout="wide")

# URL da planilha
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M2TGuEkzyOXgcxGK9ujYDknIgjvWlveHHsSpqnvv5j4/export?format=csv&gid=1575732509"

@st.cache_data(ttl=5)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [c.strip() for c in df.columns]
    
    # Tratamento da coluna VALOR TOTAL
    if 'VALOR TOTAL' in df.columns:
        df['VALOR TOTAL'] = df['VALOR TOTAL'].replace(r'[R\$\.\,]', '', regex=True).fillna(0)
        df['VALOR TOTAL'] = pd.to_numeric(df['VALOR TOTAL'], errors='coerce') / 100
    return df

try:
    df = load_data()
    st.title("📊 Painel de Fiscalização - Odontologia")
    
    # Métricas no topo
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Atendimentos", len(df))
    c2.metric("Faturamento Total", f"R$ {df['VALOR TOTAL'].sum():,.2f}")
    c3.metric("Qtd. Procedimentos", int(df['QUANTIDADE'].sum()) if 'QUANTIDADE' in df.columns else 0)

    st.divider()

    # Gráficos Dinâmicos
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Produção por Procedimento")
        fig_proc = px.bar(df, x='QUANTIDADE', y='PROCEDIMENTO', orientation='h', color='CLINICA', title="Quantidade por Tipo")
        st.plotly_chart(fig_proc, use_container_width=True)

    with col_right:
        st.subheader("Distribuição por Turma")
        fig_pie = px.pie(df, values='VALOR TOTAL', names='TURMA', hole=0.4, title="Faturamento por Semestre")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Visualização dos Dados")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao processar gráficos: {e}")
