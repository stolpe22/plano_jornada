# jornada_courses_page.py

import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from thefuzz import process, fuzz
from modules import database_manager as dbm

st.set_page_config(page_title="Cursos da Jornada", layout="wide")

# ... (as funções clean_text e calculate_word_match_score permanecem as mesmas) ...
def clean_text(text):
    """Padroniza o texto para uma correspondência difusa mais precisa."""
    if not isinstance(text, str):
        return ''
    text = text.lower().strip()
    text = text.replace(' e ', ' ').replace(' + ', ' ').replace(':', '').replace('-', ' ')
    text = text.replace('|', ' ').replace('"', '').replace("'", "")
    text = text.replace('aula', '').replace('trilha', '').replace('projeto', '').replace('workshop', '')
    text = ' '.join(text.split())
    return text

@st.cache_data
def calculate_word_match_score(search_term, text_block):
    """
    Busca o termo dentro de um bloco de texto, palavra por palavra,
    e retorna o score da palavra mais parecida encontrada.
    """
    if not search_term or not text_block:
        return 0
    words = set(text_block.split())
    if not words:
        return 0
    best_match, score = process.extractOne(search_term, words, scorer=fuzz.ratio)
    return score
    
st.title("📚 Explorador de Cursos da Jornada")
st.markdown("Filtre e pesquise por todo o conteúdo que foi extraído da plataforma.")

@st.cache_data
def load_data():
    """Carrega e prepara os dados do DB, usando cache para performance."""
    df = dbm.load_table_to_df('cursos')
    for col in ['aula_sumario', 'aula_conteudo_html', 'curso_nome', 'modulo_nome', 'aula_nome']:
        if col not in df.columns:
            df[col] = ''
        df[col] = df[col].fillna('')
    return df

# Carrega os dados da tabela 'cursos'
df_cursos = load_data()

if df_cursos.empty:
    st.warning("Os dados dos cursos ainda não foram extraídos.")
    st.info("Por favor, vá para a página 'Scraper e Junção' e execute o passo de scraping primeiro.")
else:
    # --- O restante do código da página permanece o mesmo ---
    # --- Filtros na Barra Lateral ---
    st.sidebar.header("Filtros")
    
    trilhas_disponiveis = df_cursos['trilha_nome'].dropna().unique().tolist()
    select_all = st.sidebar.checkbox("Selecionar Todas as Trilhas", value=True)
    
    default_selection = trilhas_disponiveis if select_all else []
        
    trilhas_selecionadas = st.sidebar.multiselect(
        "Filtrar por Trilha:",
        options=trilhas_disponiveis,
        default=default_selection
    )

    texto_busca = st.sidebar.text_input("Buscar por termo (ex: pyton, pipeline airflow)")
    sensibilidade = st.sidebar.slider("Sensibilidade da Busca (%)", min_value=30, max_value=100, value=80, help="Quão parecido o resultado deve ser com a sua busca. Para erros de digitação, 80-90% é um bom valor.")

    if not trilhas_selecionadas:
        df_filtrado = pd.DataFrame(columns=df_cursos.columns)
    else:
        df_filtrado = df_cursos[df_cursos['trilha_nome'].isin(trilhas_selecionadas)].copy()

    # ... (toda a lógica de busca e exibição permanece idêntica) ...
    if texto_busca:
        texto_busca_limpo = clean_text(texto_busca)
        df_filtrado['texto_pesquisavel'] = (
            df_filtrado['curso_nome'].apply(clean_text) + ' ' +
            df_filtrado['modulo_nome'].apply(clean_text) + ' ' +
            df_filtrado['aula_nome'].apply(clean_text) + ' ' +
            df_filtrado['aula_sumario'].apply(clean_text) + ' ' +
            df_filtrado['aula_conteudo_html'].apply(lambda x: clean_text(BeautifulSoup(x, 'html.parser').get_text()))
        )
        if len(texto_busca_limpo.split()) > 1:
            st.sidebar.info("Buscando por frase...")
            df_filtrado['score'] = df_filtrado['texto_pesquisavel'].apply(lambda x: fuzz.token_set_ratio(texto_busca_limpo, x))
            resultados = df_filtrado[df_filtrado['score'] >= sensibilidade]
            if resultados.empty:
                st.sidebar.warning("Nenhum resultado por frase. Tentando por aproximação...")
                df_filtrado['score'] = df_filtrado['texto_pesquisavel'].apply(lambda x: calculate_word_match_score(texto_busca_limpo, x))
                df_filtrado = df_filtrado[df_filtrado['score'] >= sensibilidade]
        else:
            st.sidebar.info("Buscando por aproximação de palavra...")
            df_filtrado['score'] = df_filtrado['texto_pesquisavel'].apply(lambda x: calculate_word_match_score(texto_busca_limpo, x))
            resultados = df_filtrado[df_filtrado['score'] >= sensibilidade]
            if resultados.empty:
                st.sidebar.warning("Nenhum resultado por aproximação. Tentando busca por frase...")
                df_filtrado['score'] = df_filtrado['texto_pesquisavel'].apply(lambda x: fuzz.token_set_ratio(texto_busca_limpo, x))
                df_filtrado = df_filtrado[df_filtrado['score'] >= sensibilidade]
        df_filtrado = df_filtrado.sort_values(by='score', ascending=False)

    st.markdown(f"**Exibindo {len(df_filtrado)} aulas encontradas:**")
    col_header = st.columns((1, 3, 3, 4, 1, 2, 1.5))
    headers = ["Feita", "Curso", "Módulo", "Aula", "Link", "Detalhes", "Relevância"]
    for col, header in zip(col_header, headers):
        col.markdown(f"**{header}**")
    st.divider()
    for index, row in df_filtrado.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns((1, 3, 3, 4, 1, 2, 1.5))
        with col1:
            st.checkbox("", value=row.get('aula_concluida', False), key=f"check_{row.get('aula_id', index)}", label_visibility="collapsed")
        with col2:
            st.markdown(row['curso_nome'])
        with col3:
            st.markdown(row['modulo_nome'])
        with col4:
            st.markdown(row['aula_nome'])
        with col5:
            if pd.notna(row['aula_link']):
                st.link_button("▶️", row['aula_link'], help="Abrir a aula na plataforma")
        with col6:
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                if pd.notna(row['aula_sumario']) and row['aula_sumario'].strip():
                    with st.popover("📝", help="Ver o sumário da aula"):
                        st.subheader("Sumário da Aula")
                        st.text(row['aula_sumario'])
            with sub_col2:
                if pd.notna(row['aula_conteudo_html']) and row['aula_conteudo_html'].strip():
                    with st.popover("📖", help="Ver o conteúdo HTML completo da aula"):
                        st.subheader("Conteúdo Completo")
                        st.markdown(row['aula_conteudo_html'], unsafe_allow_html=True)
        with col7:
            if 'score' in row and pd.notna(row['score']):
                st.progress(int(row['score']), text=f"{row['score']}%")