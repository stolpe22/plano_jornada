# modules/data_joiner.py

import pandas as pd
from thefuzz import process, fuzz
from . import database_manager as dbm

# ... (funções clean_text e encontrar_melhor_match permanecem as mesmas) ...
def clean_text(text):
    if not isinstance(text, str): return ''
    text = text.lower().strip().replace(' e ', ' ').replace(' + ', ' ').replace(':', '').replace('-', ' ')
    text = text.replace('|', ' ').replace('"', '').replace("'", "").replace('aula', '').replace('trilha', '').replace('projeto', '').replace('workshop', '')
    return ' '.join(text.split())
def encontrar_melhor_match(row, df_scraper, scraper_trilhas):
    plano_trilha = clean_text(row['Trilha'])
    plano_modulo = clean_text(row['Módulo'])
    melhor_trilha_limpa, score_trilha = process.extractOne(plano_trilha, scraper_trilhas.keys(), scorer=fuzz.token_set_ratio)
    if score_trilha < 80: return None, None
    df_trilha_especifica = scraper_trilhas[melhor_trilha_limpa]
    opcoes_de_modulo = {clean_text(mod): mod for mod in df_trilha_especifica['modulo_nome'].dropna().unique()}
    match_final_mod = None
    score_final_mod = 0
    if opcoes_de_modulo:
        melhor_modulo_limpo, score_modulo = process.extractOne(plano_modulo, opcoes_de_modulo.keys(), scorer=fuzz.token_set_ratio)
        if score_modulo > 65:
            score_final_mod = score_modulo
            nome_original_modulo = opcoes_de_modulo[melhor_modulo_limpo]
            primeira_aula = df_trilha_especifica[df_trilha_especifica['modulo_nome'] == nome_original_modulo].iloc[0]
            match_final_mod = (primeira_aula['aula_link'], primeira_aula['aula_concluida'])
    opcoes_de_curso = {clean_text(cur): cur for cur in df_trilha_especifica['curso_nome'].dropna().unique()}
    match_final_cur = None
    score_final_cur = 0
    if opcoes_de_curso:
        melhor_curso_limpo, score_curso = process.extractOne(plano_modulo, opcoes_de_curso.keys(), scorer=fuzz.token_set_ratio)
        if score_curso > 65:
            score_final_cur = score_curso
            nome_original_curso = opcoes_de_curso[melhor_curso_limpo]
            primeira_aula = df_trilha_especifica[df_trilha_especifica['curso_nome'] == nome_original_curso].iloc[0]
            match_final_cur = (primeira_aula['aula_link'], primeira_aula['aula_concluida'])
    if score_final_mod >= score_final_cur and match_final_mod is not None:
        return match_final_mod
    elif match_final_cur is not None:
        return match_final_cur
    else:
        return None, None

def run_joiner(log_area):
    log_area.text("--- Iniciando o processo de junção de dados ---")
    
    # Carrega o plano de estudos que contém os IDs e as marcações manuais
    df_plano_antigo = dbm.load_table_to_df('plano_estudos')
    df_scraper = dbm.load_table_to_df('cursos')
    
    if df_plano_antigo.empty or df_scraper.empty:
        log_area.error(f"❌ ERRO: Tabelas ('plano_estudos', 'cursos') estão vazias.")
        return None

    log_area.text("✅ Tabelas do banco de dados carregadas com sucesso.")
    
    df_scraper.dropna(subset=['trilha_nome', 'modulo_nome', 'curso_nome', 'aula_link', 'aula_concluida'], inplace=True)
    scraper_trilhas = {
        clean_text(trilha): df_scraper[df_scraper['trilha_nome'] == trilha]
        for trilha in df_scraper['trilha_nome'].unique()
    }

    log_area.text("➡️  Iniciando a correspondência difusa...")
    
    df_plano_novo = df_plano_antigo.copy()

    resultados_scraper = df_plano_novo.apply(
        lambda row: encontrar_melhor_match(row, df_scraper, scraper_trilhas), axis=1
    )
    
    df_plano_novo[['link_scraper', 'status_scraper']] = pd.DataFrame(resultados_scraper.tolist(), index=df_plano_novo.index)
    
    log_area.text("➡️  Preservando marcações manuais...")

    df_plano_novo['aula_link'] = df_plano_novo['link_scraper']
    
    df_plano_novo['aula_concluida'] = df_plano_novo.apply(
        lambda row: True if df_plano_antigo.loc[row.name, 'aula_concluida'] else row['status_scraper'],
        axis=1
    )
    df_plano_novo['aula_concluida'] = df_plano_novo['aula_concluida'].fillna(False).astype(bool)

    df_plano_novo.drop(columns=['link_scraper', 'status_scraper'], inplace=True)
    
    # --- MUDANÇA AQUI ---
    # Garante que o DataFrame final tenha as colunas na ordem correta, incluindo o 'id'
    colunas_ordenadas = ["id", "Trilha", "Módulo", "Carga Horária (h)", "Objetivo", "aula_link", "aula_concluida"]
    df_plano_final = df_plano_novo[colunas_ordenadas]

    log_area.text("✅ Correspondência finalizada, preservando IDs e marcações manuais.")
    
    # Salva o DataFrame final, que agora inclui a coluna 'id'
    dbm.save_df_to_db(df_plano_final, 'plano_estudos')
    
    links_encontrados = df_plano_final['aula_link'].notna().sum()
    total_linhas = len(df_plano_final)
    log_area.success(f"Resultados salvos na tabela 'plano_estudos'.")
    log_area.info(f"Foram encontrados links para {links_encontrados} de {total_linhas} módulos.")

    return df_plano_final