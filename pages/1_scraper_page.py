# pages/1_scraper_page.py

import streamlit as st
import pandas as pd
import time
from modules.authenticator import autenticar_jornadadedados
from modules.scraper import run_full_scraper
from modules.data_joiner import run_joiner
from modules import database_manager as dbm

st.set_page_config(page_title="Scraper", layout="wide")

st.title("🚀 Scraper e Junção de Dados")
st.markdown("Siga os passos abaixo para gerar seu plano de estudos com links.")

# --- Inicialização do Session State ---
# Guarda o estado da UI e o DataFrame temporário do upload
if 'scraping_done' not in st.session_state:
    st.session_state.scraping_done = dbm.table_exists_and_has_data('cursos')
if 'plan_uploaded' not in st.session_state:
    st.session_state.plan_uploaded = dbm.table_exists_and_has_data('plano_estudos')
if 'df_para_upload' not in st.session_state:
    st.session_state.df_para_upload = None

# --- PASSO 0: UPLOAD E CONFIRMAÇÃO DO PLANO ---
st.info("**Passo 0:** Carregue seu `plano_de_estudos.csv` para iniciar.")

uploaded_file = st.file_uploader("Escolha seu plano de estudos (CSV)", type="csv")

# Se um arquivo for carregado, ele é lido e guardado temporariamente no session_state
if uploaded_file is not None:
    try:
        # Lê o arquivo e armazena na memória da sessão para a etapa de confirmação
        st.session_state.df_para_upload = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler o arquivo CSV: {e}")
        st.session_state.df_para_upload = None # Limpa em caso de erro

# Se houver um DataFrame na memória esperando para ser carregado, mostramos a pré-visualização e o botão
if st.session_state.df_para_upload is not None:
    st.markdown("#### Pré-visualização do seu Plano")
    st.markdown("Confira se os dados abaixo estão corretos antes de carregar no sistema.")
    st.dataframe(st.session_state.df_para_upload.head())

    if st.button("✅ Inserir no Banco de Dados"):
        with st.spinner("Salvando no banco de dados..."):
            df_para_salvar = st.session_state.df_para_upload.copy()
            
            # Adiciona colunas que o sistema usará
            df_para_salvar['aula_link'] = None
            df_para_salvar['aula_concluida'] = False # Inicia todas as aulas como não concluídas

            # Salva no banco de dados
            dbm.save_df_to_db(df_para_salvar, 'plano_estudos')

            # Atualiza o estado da UI e limpa o DataFrame temporário
            st.session_state.plan_uploaded = True
            st.session_state.df_para_upload = None
            
            st.success("Seu plano foi registrado com sucesso no banco de dados!")
            time.sleep(2) # Pausa para ver os balões :)
            st.rerun()

st.divider()

# --- PASSO 1: SCRAPING (sem alterações) ---
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
            with log_container:
                # Criamos um container para o log para poder limpar depois se necessário
                log_area = st.empty()
            
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

# --- PASSO 2: JUNÇÃO DE DADOS (sem alterações) ---
st.info("**Passo 2:** Após o scraping, gere os links no seu plano de estudos.")

join_disabled = not (st.session_state.scraping_done and st.session_state.plan_uploaded)

if st.button("Gerar Links no Plano de Estudos", disabled=join_disabled):
    with st.spinner("Iniciando a correspondência difusa..."):
        join_log_area = st.expander("Log da Junção", expanded=True).empty()
        
        resultado_df = run_joiner(join_log_area)

        if resultado_df is not None:
            st.success("Processo finalizado! Seu plano com links foi salvo no banco de dados.")
            st.dataframe(resultado_df.head(10))
            
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
        st.warning("Carregue e confirme seu plano de estudos no Passo 0 para habilitar a junção.")