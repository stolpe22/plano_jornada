import streamlit as st
import os

# --- Configuração da Página Principal ---
st.set_page_config(
    page_title="Jornada Planner",
    page_icon="🚀",
    layout="wide"
)

# Garante que a pasta 'dados' exista
os.makedirs('dados', exist_ok=True)

# --- Página de Boas-Vindas ---
st.title("Bem-vindo ao Jornada Scraper & Planner 🚀")
st.markdown("---")
st.markdown(
    """
    Esta é uma ferramenta para automatizar a coleta de dados da plataforma **Jornada de Dados** e visualizar seu progresso nos estudos.
    
    ### Como usar:
    
    1.  **Navegue para a página `scraper page`** na barra lateral para começar.
    2.  Insira suas credenciais para fazer o scraping de todos os cursos.
    3.  Após o scraping, clique para fazer a junção com seu plano de estudos.
    4.  **Vá para a página `dashboard page`** para ver seu dashboard de progresso!
    
    Use o menu na barra lateral à esquerda para navegar entre as seções.
    """
)
st.sidebar.success("Selecione uma página acima.")

