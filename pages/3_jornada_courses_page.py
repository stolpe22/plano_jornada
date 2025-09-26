# pages/3_jornada_courses_page.py

import streamlit as st
import pandas as pd
from modules import database_manager as dbm

st.set_page_config(page_title="Cursos da Jornada", layout="wide")
    
st.title("📚 Explorador de Cursos da Jornada")
st.markdown("Pesquise por todo o conteúdo que foi extraído da plataforma.")

if 'texto_busca' not in st.session_state:
    st.session_state.texto_busca = ""

@st.cache_data
def load_data():
    """Carrega os dados completos dos cursos do DB, usando cache para performance."""
    df = dbm.load_table_to_df('cursos')
    for col in ['aula_sumario', 'aula_conteudo_html', 'curso_nome', 'modulo_nome', 'aula_nome']:
        if col not in df.columns:
            df[col] = ''
        df[col] = df[col].fillna('')
    return df

df_cursos_todos = load_data()

if df_cursos_todos.empty:
    st.warning("Os dados dos cursos ainda não foram extraídos.")
    st.info("Por favor, vá para a página 'Scraper e Junção' e execute o passo de scraping primeiro.")
else:
    # --- BARRA DE BUSCA NA PÁGINA PRINCIPAL ---
    st.text_input(
        "Buscar por termo:",
        key="texto_busca",
        placeholder="Digite para buscar em todo o conteúdo da Jornada..."
    )
    
    # --- FILTROS NA BARRA LATERAL ---
    st.sidebar.header("🔎 Filtros")
    trilhas_disponiveis = sorted(df_cursos_todos['trilha_nome'].dropna().unique().tolist())
    select_all = st.sidebar.checkbox("Selecionar Todas as Trilhas", value=True, key="select_all_trilhas")
    
    default_selection = trilhas_disponiveis if select_all else []
    trilhas_selecionadas = st.sidebar.multiselect(
        "Filtrar por Trilha:",
        options=trilhas_disponiveis,
        default=default_selection
    )

    st.divider()

    # --- LÓGICA DE BUSCA E FILTRO ---
    df_para_exibir = pd.DataFrame()

    if st.session_state.texto_busca:
        df_resultados_busca = dbm.search_courses(st.session_state.texto_busca)
        
        if not df_resultados_busca.empty:
            df_para_exibir = df_resultados_busca[df_resultados_busca['trilha_nome'].isin(trilhas_selecionadas)].copy()

            if not df_para_exibir.empty:
                min_rank = df_para_exibir['rank'].min()
                max_rank = df_para_exibir['rank'].max()
                
                if max_rank == min_rank:
                    df_para_exibir['score'] = 100
                else:
                    df_para_exibir['score'] = ((df_para_exibir['rank'] - max_rank) / (min_rank - max_rank) * 100).astype(int)
    else:
        df_para_exibir = df_cursos_todos[df_cursos_todos['trilha_nome'].isin(trilhas_selecionadas)]

    # --- EXIBIÇÃO DOS DADOS ---
    st.markdown(f"**Exibindo {len(df_para_exibir)} aulas encontradas:**")
    
    # <--- MUDANÇA AQUI: Ajustamos a largura das colunas e adicionamos a "Trilha"
    col_header_spec = (1, 3, 3, 3, 4, 1, 2) 
    headers = ["Feita", "Trilha", "Curso", "Módulo", "Aula", "Link", "Detalhes"]
    if st.session_state.texto_busca:
        col_header_spec += (1.5,)
        headers.append("Relevância")

    col_header = st.columns(col_header_spec)
    for col, header in zip(col_header, headers):
        col.markdown(f"**{header}**")
    st.divider()

    for index, row in df_para_exibir.iterrows():
        cols = st.columns(col_header_spec)
        
        # <--- MUDANÇA AQUI: Adicionamos a exibição da Trilha e reordenamos os índices
        cols[0].checkbox("", value=row.get('aula_concluida', False), key=f"check_{row.get('aula_id', index)}", label_visibility="collapsed")
        cols[1].markdown(row['trilha_nome'])
        cols[2].markdown(row['curso_nome'])
        cols[3].markdown(row['modulo_nome'])
        cols[4].markdown(row['aula_nome'])
        if pd.notna(row['aula_link']):
            cols[5].link_button("▶️", row['aula_link'], help="Abrir a aula na plataforma")
        with cols[6]:
            sub_col1, sub_col2 = st.columns(2)
            if pd.notna(row['aula_sumario']) and row['aula_sumario'].strip():
                with sub_col1.popover("📝", help="Ver o sumário da aula"):
                    st.subheader("Sumário da Aula")
                    st.text(row['aula_sumario'])
            if pd.notna(row['aula_conteudo_html']) and row['aula_conteudo_html'].strip():
                with sub_col2.popover("📖", help="Ver o conteúdo da aula"):
                    st.subheader("Conteúdo Completo")
                    st.markdown(row['aula_conteudo_html'])
        
        # O índice da relevância muda para 7 por causa da nova coluna
        if st.session_state.texto_busca and 'score' in row and pd.notna(row['score']):
            rank_bruto = f"{row['rank']:.2f}"
            cols[7].progress(int(row['score']), text=f"{int(row['score'])}%")
            cols[7].caption(f"Rank: {rank_bruto}", help="Pontuação de relevância do FTS5. Quanto menor o número, mais relevante.")