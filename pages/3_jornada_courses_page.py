import streamlit as st
import pandas as pd
import os
from bs4 import BeautifulSoup
from thefuzz import process, fuzz

st.set_page_config(page_title="Cursos da Jornada", layout="wide")

# --- FUNÇÃO DE LIMPEZA DE TEXTO ---
def clean_text(text):
    """Padroniza o texto para uma correspondência difusa mais precisa."""
    if not isinstance(text, str):
        return ''
    # Converte para minúsculas, remove espaços extras e caracteres comuns que atrapalham
    text = text.lower().strip()
    text = text.replace(' e ', ' ').replace(' + ', ' ').replace(':', '').replace('-', ' ')
    text = text.replace('|', ' ').replace('"', '').replace("'", "")
    # Remove palavras genéricas que podem atrapalhar a busca por termos específicos
    text = text.replace('aula', '').replace('trilha', '').replace('projeto', '').replace('workshop', '')
    # Remove múltiplos espaços
    text = ' '.join(text.split())
    return text

# --- FUNÇÃO DE BUSCA POR PALAVRA (APROXIMAÇÃO) ---
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
        
    # Usamos fuzz.ratio que é ótimo para comparar duas strings curtas (typos)
    best_match, score = process.extractOne(search_term, words, scorer=fuzz.ratio)
    return score

# --- Definição dos Caminhos ---
PATH_CURSOS_CSV = 'dados/cursos_jornada.csv'

st.title("📚 Explorador de Cursos da Jornada")
st.markdown("Filtre e pesquise por todo o conteúdo que foi extraído da plataforma.")

@st.cache_data
def load_data(path):
    """Carrega e prepara os dados, usando cache para performance."""
    df = pd.read_csv(path)
    # Garante que as colunas de texto existam e preenche valores nulos
    for col in ['aula_sumario', 'aula_conteudo_html', 'curso_nome', 'modulo_nome', 'aula_nome']:
        if col not in df.columns:
            df[col] = ''
        df[col] = df[col].fillna('')
    return df

if not os.path.exists(PATH_CURSOS_CSV):
    st.warning("O arquivo com os dados dos cursos ainda não foi gerado.")
    st.info("Por favor, vá para a página '🤖 Scraper e Junção' e execute o passo de scraping primeiro.")
else:
    df_cursos = load_data(PATH_CURSOS_CSV)

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

    texto_busca = st.sidebar.text_input("Buscar por termo (ex: pyton, airbyte, pipeline)")
    sensibilidade = st.sidebar.slider("Sensibilidade da Busca (%)", min_value=30, max_value=100, value=80, help="Quão parecido o resultado deve ser com a sua busca. Para erros de digitação, 80-90% é um bom valor.")

    # Aplicar filtros
    if not trilhas_selecionadas:
        df_filtrado = pd.DataFrame(columns=df_cursos.columns)
    else:
        df_filtrado = df_cursos[df_cursos['trilha_nome'].isin(trilhas_selecionadas)].copy()

    if texto_busca:
        texto_busca_limpo = clean_text(texto_busca)
        
        # Cria uma única coluna de texto para a busca, já limpa
        df_filtrado['texto_pesquisavel'] = (
            df_filtrado['curso_nome'].apply(clean_text) + ' ' +
            df_filtrado['modulo_nome'].apply(clean_text) + ' ' +
            df_filtrado['aula_nome'].apply(clean_text) + ' ' +
            df_filtrado['aula_sumario'].apply(clean_text) + ' ' +
            df_filtrado['aula_conteudo_html'].apply(lambda x: clean_text(BeautifulSoup(x, 'html.parser').get_text()))
        )
        
        # --- LÓGICA DE BUSCA DUPLA ---
        
        # 1. Tenta a busca por frase primeiro
        df_filtrado['score'] = df_filtrado['texto_pesquisavel'].apply(
            lambda x: fuzz.token_set_ratio(texto_busca_limpo, x)
        )
        resultados_frase = df_filtrado[df_filtrado['score'] >= sensibilidade]

        # 2. Se não achar nada, tenta a busca por aproximação de palavra
        if resultados_frase.empty:
            st.sidebar.warning("Nenhum resultado por frase. Tentando busca por aproximação...")
            df_filtrado['score'] = df_filtrado['texto_pesquisavel'].apply(
                lambda x: calculate_word_match_score(texto_busca_limpo, x)
            )
            df_filtrado = df_filtrado[df_filtrado['score'] >= sensibilidade].sort_values(by='score', ascending=False)
        else:
            st.sidebar.success("Resultados encontrados por busca de frase.")
            df_filtrado = resultados_frase.sort_values(by='score', ascending=False)

    # --- Exibição dos Dados ---
    st.markdown(f"**Exibindo {len(df_filtrado)} aulas encontradas:**")

    # Adiciona a coluna de Relevância
    col_header = st.columns((1, 3, 3, 5, 1, 2, 1)) # <-- Proporção da coluna de relevância diminuída
    headers = ["Feita", "Curso", "Módulo", "Aula", "Link", "Detalhes", "Relevância"]
    for col, header in zip(col_header, headers):
        col.markdown(f"**{header}**")
    st.divider()

    for index, row in df_filtrado.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns((1, 3, 3, 5, 1, 2, 1)) # <-- Proporção da coluna de relevância diminuída
        
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

