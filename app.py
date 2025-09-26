# app.py

import streamlit as st
from modules import database_manager as dbm

# --- Configuração da Página Principal ---
st.set_page_config(
    page_title="Jornada Planner",
    page_icon="🚀",
    layout="wide"
)

# Garante que o banco de dados e as tabelas existam
dbm.init_db()

# --- Página de Boas-Vindas ---
st.title("Bem-vindo ao Jornada Scraper & Planner 🚀")
st.markdown("---")
st.markdown(
    """
    Esta é uma ferramenta para automatizar a coleta de dados da plataforma **Jornada de Dados** e visualizar seu progresso nos estudos.
    
    ### Como usar:
    
    1.  **Navegue para a página `Scraper e Junção`** na barra lateral para começar.
    2.  **(Primeira vez)** Faça o upload do seu arquivo `plano_de_estudos.csv`.
    3.  Insira suas credenciais para fazer o scraping de todos os cursos e módulos.
    4.  Após o scraping, clique para gerar os links e status no seu plano.
    5.  **Vá para a página `Dashboard`** para ver seu progresso!
    6.  **Use a página `Cursos da Jornada`** para pesquisar todo o conteúdo da plataforma.
    
    Use o menu na barra lateral à esquerda para navegar entre as seções.
    """
)
st.sidebar.success("Selecione uma página acima.")