# dashboard_page.py

import streamlit as st
import pandas as pd
from modules import database_manager as dbm

st.set_page_config(page_title="Plano de Estudos", layout="wide")

st.title("📊 Dashboard do Plano de Estudos")

# Carrega os dados da tabela 'plano_estudos'
df_plano = dbm.load_table_to_df('plano_estudos')

if df_plano.empty:
    st.warning("Ainda não há um plano de estudos no banco de dados.")
    st.info("Por favor, vá para a página 'Scraper e Junção' e carregue seu arquivo .csv.")
else:
    # Garante que a coluna 'aula_concluida' existe e trata valores nulos
    if 'aula_concluida' in df_plano.columns:
        df_plano['aula_concluida'] = df_plano['aula_concluida'].fillna(False).astype(bool)
        df_plano['Carga Horária (h)'] = pd.to_numeric(df_plano['Carga Horária (h)'], errors='coerce').fillna(0)

        # --- Métricas Principais ---
        st.markdown("### Métricas Gerais")
        
        total_aulas = len(df_plano)
        aulas_concluidas = int(df_plano['aula_concluida'].sum())
        aulas_pendentes = total_aulas - aulas_concluidas
        progresso_percentual = (aulas_concluidas / total_aulas) * 100 if total_aulas > 0 else 0
        
        total_horas = df_plano['Carga Horária (h)'].sum()
        horas_restantes = df_plano[df_plano['aula_concluida'] == False]['Carga Horária (h)'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Aulas Concluídas", f"{aulas_concluidas}", f"de {total_aulas} aulas")
        col2.metric("Aulas Pendentes", f"{aulas_pendentes}")
        col3.metric("Horas Restantes", f"{horas_restantes:.1f}h")

        st.markdown("##### Progresso Total do Plano")
        st.progress(progresso_percentual / 100, text=f"{progresso_percentual:.1f}% Concluído")
        
        st.divider()

        # --- Análise por Trilha ---
        st.markdown("### Progresso por Trilha")
        
        progresso_trilha = df_plano.groupby('Trilha').agg(
            total_aulas=('Módulo', 'count'),
            aulas_concluidas=('aula_concluida', lambda x: x.sum())
        ).reset_index()

        progresso_trilha['progresso_%'] = progresso_trilha.apply(
            lambda row: (row['aulas_concluidas'] / row['total_aulas'] * 100) if row['total_aulas'] > 0 else 0,
            axis=1
        ).round(1)

        for index, row in progresso_trilha.iterrows():
            st.markdown(f"**{row['Trilha']}**")
            st.progress(row['progresso_%'] / 100, text=f"{row['progresso_%']}% concluído ({int(row['aulas_concluidas'])} de {int(row['total_aulas'])} aulas)")

        st.divider()

        # --- Tabela Detalhada ---
        st.markdown("### Detalhes do Plano de Estudos")
        st.data_editor(
            df_plano,
            column_config={
                "aula_link": st.column_config.LinkColumn(
                    "Link da Aula",
                    help="Clique para abrir a aula na plataforma",
                    display_text="▶️ Abrir Aula"
                ),
                "aula_concluida": st.column_config.CheckboxColumn(
                    "Concluída?",
                    default=False,
                )
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.error("A coluna 'aula_concluida' não foi encontrada. Por favor, gere os links novamente na página de Scraper.")