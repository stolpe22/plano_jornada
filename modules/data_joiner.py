import pandas as pd
from thefuzz import process, fuzz

def clean_text(text):
    if not isinstance(text, str):
        return ''
    text = text.lower().strip()
    text = text.replace(' e ', ' ').replace(' + ', ' ').replace(':', '').replace('-', ' ')
    text = text.replace('|', ' ').replace('"', '').replace("'", "")
    text = text.replace('aula', '').replace('trilha', '').replace('projeto', '').replace('workshop', '')
    text = ' '.join(text.split())
    return text

def encontrar_melhor_link(row, df_scraper, scraper_trilhas, log_area):
    plano_trilha = clean_text(row['Trilha'])
    plano_modulo = clean_text(row['Módulo'])

    log_area.info(f"Buscando: Trilha '{row['Trilha']}' | Módulo '{row['Módulo']}'")
    
    melhor_trilha_limpa, score_trilha = process.extractOne(plano_trilha, scraper_trilhas.keys(), scorer=fuzz.token_set_ratio)
    
    if score_trilha < 80:
        return None

    df_trilha_especifica = scraper_trilhas[melhor_trilha_limpa]
    
    opcoes_de_modulo = {clean_text(mod): mod for mod in df_trilha_especifica['modulo_nome'].dropna().unique()}
    link_final_mod = None
    score_final_mod = 0
    if opcoes_de_modulo:
        melhor_modulo_limpo, score_modulo = process.extractOne(plano_modulo, opcoes_de_modulo.keys(), scorer=fuzz.token_set_ratio)
        if score_modulo > 65:
            score_final_mod = score_modulo
            nome_original_modulo = opcoes_de_modulo[melhor_modulo_limpo]
            primeira_aula = df_trilha_especifica[df_trilha_especifica['modulo_nome'] == nome_original_modulo].iloc[0]
            link_final_mod = primeira_aula['aula_link']

    opcoes_de_curso = {clean_text(cur): cur for cur in df_trilha_especifica['curso_nome'].dropna().unique()}
    link_final_cur = None
    score_final_cur = 0
    if opcoes_de_curso:
        melhor_curso_limpo, score_curso = process.extractOne(plano_modulo, opcoes_de_curso.keys(), scorer=fuzz.token_set_ratio)
        if score_curso > 65:
            score_final_cur = score_curso
            nome_original_curso = opcoes_de_curso[melhor_curso_limpo]
            primeira_aula = df_trilha_especifica[df_trilha_especifica['curso_nome'] == nome_original_curso].iloc[0]
            link_final_cur = primeira_aula['aula_link']
            
    if score_final_mod > score_final_cur:
        return link_final_mod
    elif score_final_cur > score_final_mod:
        return link_final_cur
    else:
        return link_final_mod if score_final_mod > 0 else None

def run_joiner(log_area):
    log_area.info("--- Iniciando o processo de junção de dados ---")
    try:
        df_plano = pd.read_csv('dados/plano_de_estudos.csv')
        df_scraper = pd.read_csv('dados/cursos_jornada.csv')
        log_area.info("✅ Arquivos CSV carregados com sucesso.")
    except FileNotFoundError as e:
        log_area.error(f"❌ ERRO: Arquivo não encontrado: {e.filename}.")
        return None

    df_scraper.dropna(subset=['trilha_nome', 'modulo_nome', 'curso_nome', 'aula_link'], inplace=True)
    scraper_trilhas = {
        clean_text(trilha): df_scraper[df_scraper['trilha_nome'] == trilha]
        for trilha in df_scraper['trilha_nome'].unique()
    }

    log_area.info("➡️  Iniciando a correspondência difusa...")
    df_plano['aula_link'] = df_plano.apply(
        lambda row: encontrar_melhor_link(row, df_scraper, scraper_trilhas, log_area),
        axis=1
    )
    log_area.info("✅ Correspondência finalizada.")
    
    output_path = 'dados/plano_de_estudos_com_links.csv'
    df_plano.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    links_encontrados = df_plano['aula_link'].notna().sum()
    total_linhas = len(df_plano)
    log_area.success(f"Resultados salvos em '{output_path}'")
    log_area.info(f"Foram encontrados links para {links_encontrados} de {total_linhas} módulos do plano.")

    return output_path, df_plano