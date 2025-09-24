import streamlit as st
import pandas as pd
import os

# Importa as funções dos nossos módulos
from modules.authenticator import autenticar_jornadadedados
from modules.scraper import run_full_scraper  # <-- Importamos a função principal
from modules.data_joiner import run_joiner

# Configuração da página
st.set_page_config(page_title="Jornada Scraper", layout="centered")

# --- Lógica do Streamlit ---
st.title("🚀 Scraper da Jornada de Dados")
st.markdown("Uma ferramenta para extrair os dados de cursos e enriquecer seu plano de estudos.")

# Define os caminhos dos arquivos
PATH_CURSOS_CSV = 'dados/cursos_jornada.csv'
PATH_PLANO_CSV = 'dados/plano_de_estudos_com_links.csv'
PATH_PLANO_INPUT = 'dados/plano_de_estudos.csv'

# Garante que a pasta 'dados' exista
os.makedirs('dados', exist_ok=True)

# Usa o session_state para que o Streamlit "lembre" que o scraping foi feito
if 'scraping_done' not in st.session_state:
    st.session_state.scraping_done = os.path.exists(PATH_CURSOS_CSV)

st.info("**Passo 1:** Faça o scraping dos dados da plataforma. Isso pode levar vários minutos.")

with st.form("login_form"):
    email = st.text_input("Seu E-mail da Plataforma", key="email")
    senha = st.text_input("Sua Senha da Plataforma", type="password", key="senha")
    submitted = st.form_submit_button("Fazer Scraping Agora")

    if submitted:
        if not email or not senha:
            st.error("Por favor, preencha o e-mail e a senha.")
        else:
            # Cria uma área para o log
            log_container = st.expander("Ver Log de Atividade", expanded=True)
            log_area = log_container.empty()
            
            with st.spinner("Autenticando e iniciando a raspagem... Por favor, aguarde."):
                log_area.text("Iniciando autenticação...")
                session = autenticar_jornadadedados(email, senha)
                
                if not session:
                    st.error("Falha na autenticação! Verifique suas credenciais.")
                else:
                    st.success("Autenticação bem-sucedida!")
                    
                    # --- CHAMADA REAL DO SCRAPER ---
                    df_raspado = run_full_scraper(session, log_area)
                    # --- FIM DA CHAMADA ---
                    
                    if df_raspado is not None and not df_raspado.empty:
                        df_raspado.to_csv(PATH_CURSOS_CSV, index=False, encoding='utf-8-sig')
                        st.success(f"Scraping finalizado! Dados salvos em `{PATH_CURSOS_CSV}`.")
                        st.dataframe(df_raspado.head())
                        st.session_state.scraping_done = True
                        st.rerun()
                    else:
                        st.error("A raspagem não retornou nenhum dado. Verifique o log de atividade.")

st.divider()

st.info("**Passo 2:** Após o scraping, gere os links no seu plano de estudos.")

if st.button("Gerar Links no Plano de Estudos", disabled=not st.session_state.scraping_done):
    if not os.path.exists(PATH_PLANO_INPUT):
        st.error(f"Arquivo '{PATH_PLANO_INPUT}' não encontrado! Por favor, crie a pasta 'dados' e coloque seu plano de estudos lá.")
    else:
        with st.spinner("Iniciando a correspondência difusa..."):
            join_log_area = st.expander("Log da Junção", expanded=True)
            
            resultado = run_joiner(join_log_area)

            if resultado:
                output_path, df_final = resultado
                st.success(f"Processo finalizado! Seu plano de estudos com links foi salvo em `{output_path}`.")
                st.dataframe(df_final.head(10))

                with open(output_path, "rb") as file:
                    st.download_button(
                        label="Baixar CSV com Links",
                        data=file,
                        file_name=os.path.basename(output_path),
                        mime='text/csv',
                    )
else:
    if not st.session_state.scraping_done:
        st.warning("O botão 'Gerar Links' será habilitado após o scraping ser concluído com sucesso.")
