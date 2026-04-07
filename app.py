import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Fiscalização", layout="wide")

# URL da planilha
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M2TGuEkzyOXgcxGK9ujYDknIgjvWlveHHsSpqnvv5j4/export?format=csv&gid=1575732509"

@st.cache_data(ttl=5) # Atualiza quase em tempo real
def load_data():
    # Lê a planilha pulando linhas vazias e garantindo que o cabeçalho seja a primeira linha com dados
    df = pd.read_csv(SHEET_URL)
    
    # Tenta limpar a coluna de valor se ela existir, independente de maiúsculas/minúsculas
    df.columns = [c.strip() for c in df.columns] # Remove espaços extras nos nomes
    
    col_valor = next((c for c in df.columns if 'valor' in c.lower()), None)
    
    if col_valor:
        df[col_valor] = df[col_valor].replace(r'[R\$\.\,]', '', regex=True).fillna(0)
        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce') / 100
        
    return df, col_valor

try:
    df, col_valor = load_data()

    st.title("📊 Painel de Controle - Fiscalização de Pagamentos")
    
    # Exibe métricas apenas se encontrar os dados
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de Linhas", len(df))
            
        if col_valor:
            with col2:
                st.metric("Valor Total", f"R$ {df[col_valor].sum():,.2f}")
        
        st.divider()
        
        # Mostra a tabela para você conferir se os dados estão entrando
        st.subheader("Dados da Planilha")
        st.dataframe(df)
        
    else:
        st.warning("A planilha parece estar vazia ou o link está incorreto.")

except Exception as e:
    st.error(f"Erro inesperado: {e}")
