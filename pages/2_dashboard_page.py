# pages/2_dashboard_page.py

import streamlit as st
import pandas as pd
from modules import database_manager as dbm

st.set_page_config(page_title="Plano de Estudos", layout="wide")

st.title("📊 Dashboard do Plano de Estudos")

def carregar_plano():
    df = dbm.load_table_to_df('plano_estudos')
    if not df.empty and 'aula_concluida' in df.columns:
        df['aula_concluida'] = df['aula_concluida'].fillna(False).astype(bool)
        df['Carga Horária (h)'] = pd.to_numeric(df['Carga Horária (h)'], errors='coerce').fillna(0)
    return df

df_plano = carregar_plano()

if df_plano.empty:
    st.warning("Ainda não há um plano de estudos no banco de dados.")
    st.info("Por favor, vá para a página 'Scraper e Junção' e carregue seu arquivo .csv.")
else:
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
    progresso_trilha = df_plano.groupby('Trilha').agg(total_aulas=('Módulo', 'count'), aulas_concluidas=('aula_concluida', 'sum')).reset_index()
    progresso_trilha['progresso_%'] = progresso_trilha.apply(lambda row: (row['aulas_concluidas'] / row['total_aulas'] * 100) if row['total_aulas'] > 0 else 0, axis=1).round(1)
    for index, row in progresso_trilha.iterrows():
        st.markdown(f"**{row['Trilha']}**")
        st.progress(row['progresso_%'] / 100, text=f"{row['progresso_%']}% concluído ({int(row['aulas_concluidas'])} de {int(row['total_aulas'])} aulas)")
    st.divider()

    # --- Tabela Detalhada Interativa com ID ---
    st.markdown("### Detalhes do Plano de Estudos")
    
    # Guarda o estado original no session_state para comparação
    if 'plano_original' not in st.session_state:
        st.session_state.plano_original = df_plano.copy()

    df_editado = st.data_editor(
        df_plano,
        column_config={
            # --- MUDANÇA AQUI ---
            # Escondemos a coluna 'id' do usuário, mas ela ainda existe nos dados
            "id": None,
            "aula_link": st.column_config.LinkColumn("Link da Aula", display_text="▶️ Abrir Aula"),
            "aula_concluida": st.column_config.CheckboxColumn("Concluída?", default=False)
        },
        hide_index=True,
        use_container_width=True,
        key="editor_plano"
    )

    # Compara o DataFrame de antes com o de depois para encontrar mudanças
    if not st.session_state.plano_original.equals(df_editado):
        # Encontra as linhas alteradas (comparando pela coluna 'aula_concluida')
        mudancas = st.session_state.plano_original['aula_concluida'] != df_editado['aula_concluida']
        linhas_alteradas = df_editado[mudancas]
        
        for index, row in linhas_alteradas.iterrows():
            item_id = row['id']
            novo_status = row['aula_concluida']
            
            # Salva a mudança no banco de dados usando o ID
            dbm.update_aula_status(item_id, novo_status)

        # Atualiza o estado da sessão com os novos dados e força um recarregamento para as métricas
        st.session_state.plano_original = df_editado.copy()
        st.rerun()