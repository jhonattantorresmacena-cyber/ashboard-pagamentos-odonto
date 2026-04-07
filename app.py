import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Fiscalização", layout="wide")

# URL da sua planilha (ajustada para exportação CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M2TGuEkzyOXgcxGK9ujYDknIgjvWlveHHsSpqnvv5j4/export?format=csv&gid=1575732509"

@st.cache_data(ttl=60) # Atualiza os dados a cada 60 segundos
def load_data():
    df = pd.read_csv(SHEET_URL)
    # Limpeza básica: remove cifrões e converte para numérico
    if 'Valor' in df.columns:
        df['Valor'] = df['Valor'].replace(r'[R\$\.\,]', '', regex=True).astype(float) / 100
    return df

try:
    df = load_data()

    st.title("📊 Painel de Controle - Fiscalização de Pagamentos")
    st.markdown(f"**Última atualização:** {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # --- MÉTRICAS PRINCIPAIS ---
    total_financeiro = df['Valor'].sum()
    total_procedimentos = df['Quantidade de procedimento'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Valor Total Acumulado", f"R$ {total_financeiro:,.2f}")
    col2.metric("Total de Procedimentos", int(total_procedimentos))
    col3.metric("Média por Atendimento", f"R$ {(total_financeiro/total_procedimentos):,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Produção por Procedimento")
        fig_proc = px.bar(df.groupby('Procedimento')['Quantidade de procedimento'].sum().reset_index(), 
                          x='Quantidade de procedimento', y='Procedimento', orientation='h',
                          color='Quantidade de procedimento', color_continuous_scale='Viridis')
        st.plotly_chart(fig_proc, use_container_width=True)

    with col_right:
        st.subheader("Faturamento por Clínica")
        fig_clinica = px.pie(df, values='Valor', names='Clínica', hole=0.4)
        st.plotly_chart(fig_clinica, use_container_width=True)

    # --- TABELA DE DADOS ---
    st.subheader("Visualização dos Dados Brutos")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Verifique se a planilha está compartilhada corretamente.")
