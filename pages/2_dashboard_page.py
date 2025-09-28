# pages/2_dashboard_page.py

import streamlit as st
import pandas as pd
from modules import database_manager as dbm

st.set_page_config(page_title="Plano de Estudos", layout="wide")

st.title("📊 Dashboard do Plano de Estudos")

# Inicializa o estado do filtro no session_state
if 'mostrar_concluidos' not in st.session_state:
    st.session_state.mostrar_concluidos = False

def carregar_plano():
    df = dbm.load_table_to_df('plano_estudos')
    if not df.empty and 'aula_concluida' in df.columns:
        df['aula_concluida'] = df['aula_concluida'].fillna(False).astype(bool)
        df['Carga Horária (h)'] = pd.to_numeric(df['Carga Horária (h)'], errors='coerce').fillna(0)
        df['Status'] = df['aula_concluida'].apply(lambda x: "✅ Concluído" if x else "🕒 Pendente")
    return df

df_plano = carregar_plano()

if df_plano.empty:
    st.warning("Ainda não há um plano de estudos no banco de dados.")
    st.info("Por favor, vá para a página 'Scraper e Junção' e carregue seu arquivo .csv.")
else:
    # --- MUDANÇA AQUI: Adiciona o novo filtro de Trilha na barra lateral ---
    st.sidebar.header("🔎 Filtros do Dashboard")
    trilhas_disponiveis = sorted(df_plano['Trilha'].dropna().unique().tolist())
    select_all = st.sidebar.checkbox("Selecionar Todas as Trilhas", value=True, key="select_all_trilhas_dash")
    
    default_selection = trilhas_disponiveis if select_all else []
    trilhas_selecionadas = st.sidebar.multiselect(
        "Filtrar por Trilha:",
        options=trilhas_disponiveis,
        default=default_selection,
        key="multiselect_trilhas_dash"
    )

    # --- Métricas e Progresso (sem alterações) ---
    st.markdown("### Métricas Gerais")
    total_aulas = len(df_plano)
    aulas_concluidas = int(df_plano['aula_concluida'].sum())
    aulas_pendentes = total_aulas - aulas_concluidas
    progresso_percentual = (aulas_concluidas / total_aulas) * 100 if total_aulas > 0 else 0
    horas_restantes = df_plano[~df_plano['aula_concluida']]['Carga Horária (h)'].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Aulas Concluídas", f"{aulas_concluidas}", f"de {total_aulas} aulas")
    col2.metric("Aulas Pendentes", f"{aulas_pendentes}")
    col3.metric("Horas Restantes", f"{horas_restantes:.1f}h")
    st.markdown("##### Progresso Total do Plano")
    st.progress(progresso_percentual / 100, text=f"{progresso_percentual:.1f}% Concluído")
    st.divider()
    st.markdown("### Progresso por Trilha")
    # Filtra o progresso para mostrar apenas as trilhas selecionadas
    progresso_trilha_filtrado = df_plano[df_plano['Trilha'].isin(trilhas_selecionadas)]
    progresso_trilha = progresso_trilha_filtrado.groupby('Trilha').agg(total_aulas=('Módulo', 'count'), aulas_concluidas=('aula_concluida', 'sum')).reset_index()
    progresso_trilha['progresso_%'] = progresso_trilha.apply(lambda row: (row['aulas_concluidas'] / row['total_aulas'] * 100) if row['total_aulas'] > 0 else 0, axis=1).round(1)
    for index, row in progresso_trilha.iterrows():
        st.markdown(f"**{row['Trilha']}**")
        st.progress(row['progresso_%'] / 100, text=f"{row['progresso_%']}% concluído ({int(row['aulas_concluidas'])} de {int(row['total_aulas'])} aulas)")
    st.divider()

    st.markdown("### Detalhes do Plano de Estudos")
    st.toggle("Mostrar aulas concluídas", key="mostrar_concluidos")

    # --- MUDANÇA AQUI: A lógica de filtro agora inclui as trilhas selecionadas ---
    df_para_exibir = df_plano.copy()

    # 1. Filtro de trilhas selecionadas na barra lateral
    if trilhas_selecionadas:
        df_para_exibir = df_para_exibir[df_para_exibir['Trilha'].isin(trilhas_selecionadas)]
    else:
        # Se nada for selecionado, mostra uma tabela vazia
        df_para_exibir = df_para_exibir.head(0)

    # 2. Filtro de concluídos
    if not st.session_state.mostrar_concluidos:
        df_para_exibir = df_para_exibir[df_para_exibir['aula_concluida'] == False]
    
    if 'plano_original' not in st.session_state:
        st.session_state.plano_original = df_plano.copy()

    df_editado = st.data_editor(
        df_para_exibir,
        column_config={
            "id": None, "Status": st.column_config.TextColumn("Status", width="medium"),
            "aula_link": st.column_config.LinkColumn("Link da Aula", display_text="▶️ Abrir"),
            "aula_concluida": st.column_config.CheckboxColumn("Marcar/Desmarcar", default=False),
            "Trilha": st.column_config.TextColumn("Trilha", width="large"),
            "Módulo": st.column_config.TextColumn("Módulo", width="large"),
            "Objetivo": st.column_config.TextColumn("Objetivo", width="large"),
            "Carga Horária (h)": st.column_config.NumberColumn("Horas", format="%.1f h"),
            "Dias Necessários": st.column_config.TextColumn("Dias"),
        },
        column_order=[
            "aula_concluida", "Status", "Trilha", "Módulo", "aula_link","Objetivo", "Carga Horária (h)", 
            "Dias Necessários"
        ],
        hide_index=True,
        use_container_width=True,
        key="editor_plano"
    )

    # Lógica de detecção de mudanças (sem alterações)
    df_original_exibido = st.session_state.plano_original.loc[df_editado.index]
    if not df_original_exibido.equals(df_editado):
        mudancas = df_original_exibido['aula_concluida'] != df_editado['aula_concluida']
        linhas_alteradas = df_editado[mudancas]
        
        for index, row in linhas_alteradas.iterrows():
            item_id = row['id']
            novo_status = row['aula_concluida']
            dbm.update_aula_status(item_id, novo_status)

        st.session_state.plano_original = carregar_plano().copy()
        st.rerun()