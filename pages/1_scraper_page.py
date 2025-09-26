# scraper_page.py

import streamlit as st
import pandas as pd
import os

from modules.authenticator import autenticar_jornadadedados
from modules.scraper import run_full_scraper
from modules.data_joiner import run_joiner
from modules import database_manager as dbm # Importa o novo módulo

st.set_page_config(page_title="Scraper", layout="wide")

st.title("🚀 Scraper e Junção de Dados")
st.markdown("Siga os passos abaixo para gerar seu plano de estudos com links.")

# Usa o session_state para controlar o estado da UI
if 'scraping_done' not in st.session_state:
    st.session_state.scraping_done = dbm.table_exists_and_has_data('cursos')
if 'plan_uploaded' not in st.session_state:
    st.session_state.plan_uploaded = dbm.table_exists_and_has_data('plano_estudos')

# --- PASSO 0: UPLOAD DO PLANO DE ESTUDOS ---
st.info("**Passo 0 (Opcional):** Carregue seu arquivo `plano_de_estudos.csv`.")
st.markdown("Se você já carregou seu plano antes, pode pular este passo.")

uploaded_file = st.file_uploader("Escolha seu plano de estudos (CSV)", type="csv")
if uploaded_file is not None:
    try:
        df_plano_inicial = pd.read_csv(uploaded_file)
        # Adiciona colunas vazias que serão preenchidas depois
        df_plano_inicial['aula_link'] = None
        df_plano_inicial['aula_concluida'] = None
        dbm.save_df_to_db(df_plano_inicial, 'plano_estudos')
        st.session_state.plan_uploaded = True
        st.success("Seu plano de estudos foi carregado e salvo no banco de dados com sucesso!")
        st.dataframe(df_plano_inicial.head())
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar seu arquivo: {e}")

st.divider()

# --- PASSO 1: SCRAPING ---
st.info("**Passo 1:** Faça o scraping dos dados da plataforma. Isso pode levar vários minutos.")
with st.form("login_form"):
    email = st.text_input("Seu E-mail da Plataforma", key="email")
    senha = st.text_input("Sua Senha da Plataforma", type="password", key="senha")
    submitted = st.form_submit_button("Fazer Scraping Agora")

    if submitted:
        if not email or not senha:
            st.error("Por favor, preencha o e-mail e a senha.")
        else:
            log_container = st.expander("Ver Log de Atividade", expanded=True)
            log_area = log_container.empty()
            
            with st.spinner("Autenticando e iniciando a raspagem... Por favor, aguarde."):
                log_area.text("Iniciando autenticação...")
                session = autenticar_jornadadedados(email, senha)
                
                if not session:
                    st.error("Falha na autenticação! Verifique suas credenciais.")
                else:
                    st.success("Autenticação bem-sucedida!")
                    df_raspado = run_full_scraper(session, log_area)
                    
                    if df_raspado is not None and not df_raspado.empty:
                        dbm.save_df_to_db(df_raspado, 'cursos')
                        st.success("Scraping finalizado! Dados salvos na tabela 'cursos' do banco de dados.")
                        st.dataframe(df_raspado.head())
                        st.session_state.scraping_done = True
                        st.rerun()
                    else:
                        st.error("A raspagem não retornou nenhum dado. Verifique o log de atividade.")

st.divider()

# --- PASSO 2: JUNÇÃO DE DADOS ---
st.info("**Passo 2:** Após o scraping, gere os links no seu plano de estudos.")

# O botão fica habilitado se o scraping foi feito e o plano de estudos existe no DB
join_disabled = not (st.session_state.scraping_done and st.session_state.plan_uploaded)

if st.button("Gerar Links no Plano de Estudos", disabled=join_disabled):
    with st.spinner("Iniciando a correspondência difusa..."):
        join_log_area = st.expander("Log da Junção", expanded=True).empty()
        
        resultado_df = run_joiner(join_log_area)

        if resultado_df is not None:
            st.success("Processo finalizado! Seu plano com links foi salvo no banco de dados.")
            st.dataframe(resultado_df.head(10))
            
            # Prepara o arquivo para download
            csv_para_download = resultado_df.to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label="Baixar CSV com Links",
                data=csv_para_download,
                file_name="plano_de_estudos_com_links.csv",
                mime='text/csv',
            )
else:
    if not st.session_state.scraping_done:
        st.warning("O botão 'Gerar Links' será habilitado após o scraping ser concluído.")
    if not st.session_state.plan_uploaded:
        st.warning("Carregue seu plano de estudos no Passo 0 para habilitar a junção.")