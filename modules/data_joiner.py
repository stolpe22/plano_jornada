import pandas as pd
from thefuzz import process, fuzz

def clean_text(text):
    """Padroniza o texto para melhorar a correspondência."""
    if not isinstance(text, str):
        return ''
    # Converte para minúsculas, remove espaços extras e caracteres que atrapalham
    text = text.lower().strip()
    text = text.replace(' e ', ' ').replace(' + ', ' ').replace(':', '').replace('-', ' ')
    text = text.replace('|', ' ').replace('"', '').replace("'", "")
    # Remove palavras genéricas que podem atrapalhar
    text = text.replace('aula', '').replace('trilha', '').replace('projeto', '').replace('workshop', '')
    # Remove múltiplos espaços
    text = ' '.join(text.split())
    return text

def encontrar_melhor_match(row, df_scraper, scraper_trilhas, log_area):
    """
    Para uma linha do plano, encontra o link e o status da primeira aula do módulo que melhor corresponde.
    Retorna uma tupla (link, status).
    """
    plano_trilha = clean_text(row['Trilha'])
    plano_modulo = clean_text(row['Módulo'])

    log_area.text(f"Buscando: Trilha '{row['Trilha']}' | Módulo '{row['Módulo']}'")
    
    melhor_trilha_limpa, score_trilha = process.extractOne(plano_trilha, scraper_trilhas.keys(), scorer=fuzz.token_set_ratio)
    
    if score_trilha < 80:
        return None, None

    df_trilha_especifica = scraper_trilhas[melhor_trilha_limpa]
    
    # Estratégia 1: Tentar Match Módulo-vs-Módulo
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

    # Estratégia 2: Tentar Match Módulo-vs-Curso
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
            
    # Decisão Final: Escolher a estratégia com a maior pontuação
    if score_final_mod > score_final_cur:
        log_area.text(f"  ✅ Match via Módulo (Score: {score_final_mod})")
        return match_final_mod
    elif score_final_cur > score_final_mod:
        log_area.text(f"  ✅ Match via Curso (Score: {score_final_cur})")
        return match_final_cur
    else:
        if score_final_mod > 0:
             log_area.text(f"  ✅ Match via Módulo (Scores iguais)")
             return match_final_mod
        log_area.text("  ❌ Nenhuma correspondência encontrada.")
        return None, None

def run_joiner(log_area):
    log_area.text("--- Iniciando o processo de junção de dados ---")
    try:
        df_plano = pd.read_csv('dados/plano_de_estudos.csv')
        df_scraper = pd.read_csv('dados/cursos_jornada.csv')
        log_area.text("✅ Arquivos CSV carregados com sucesso.")
    except FileNotFoundError as e:
        log_area.error(f"❌ ERRO: Arquivo não encontrado: {e.filename}.")
        return None

    # Valida colunas essenciais, incluindo a nova 'aula_concluida'
    required_cols = ['trilha_nome', 'modulo_nome', 'curso_nome', 'aula_link', 'aula_concluida']
    if not all(col in df_scraper.columns for col in required_cols):
        log_area.error("❌ ERRO: 'cursos_jornada.csv' está desatualizado. Faltam colunas.")
        log_area.info("➡️  Solução: Rode o scraper novamente para gerar um arquivo novo e completo.")
        return None

    df_scraper.dropna(subset=required_cols, inplace=True)
    scraper_trilhas = {
        clean_text(trilha): df_scraper[df_scraper['trilha_nome'] == trilha]
        for trilha in df_scraper['trilha_nome'].unique()
    }

    log_area.text("➡️  Iniciando a correspondência difusa...")
    
    # Aplica a função que retorna uma tupla (link, status)
    resultados = df_plano.apply(
        lambda row: encontrar_melhor_match(row, df_scraper, scraper_trilhas, log_area),
        axis=1
    )
    
    # Desempacota a tupla em duas novas colunas no DataFrame
    df_plano[['aula_link', 'aula_concluida']] = pd.DataFrame(resultados.tolist(), index=df_plano.index)
    
    log_area.text("✅ Correspondência finalizada.")
    
    output_path = 'dados/plano_de_estudos_com_links.csv'
    df_plano.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    links_encontrados = df_plano['aula_link'].notna().sum()
    total_linhas = len(df_plano)
    log_area.success(f"Resultados salvos em '{output_path}'")
    log_area.info(f"Foram encontrados links para {links_encontrados} de {total_linhas} módulos do plano.")

    return output_path, df_plano

