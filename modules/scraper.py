import requests
from bs4 import BeautifulSoup
import json
import time
import html as html_parser
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Funções de Extração ---

def extrair_componentes_modulos(html):
    """Extrai os dados de inicialização de todos os componentes de módulo."""
    soup = BeautifulSoup(html, 'html.parser')
    dados_dos_modulos = []
    divs_componentes = soup.find_all("div", attrs={"wire:initial-data": True})
    for div in divs_componentes:
        try:
            dados = json.loads(html_parser.unescape(div['wire:initial-data']))
            if dados.get('fingerprint', {}).get('name') == 'v2.portal.course-module-card':
                id_modulo = dados.get('serverMemo', {}).get('dataMeta', {}).get('models', {}).get('module', {}).get('id')
                if id_modulo:
                    dados['id_modulo'] = id_modulo
                    dados_dos_modulos.append(dados)
        except Exception:
            pass
    return dados_dos_modulos

def extrair_aulas_com_status(html):
    """Extrai uma lista de dicionários, cada um com o ID da aula e seu status de conclusão."""
    soup = BeautifulSoup(html, 'html.parser')
    aulas = []
    for li in soup.find_all("li", attrs={"wire:key": lambda k: k and 'lesson.' in k}):
        try:
            lesson_id = int(li["wire:key"].split("lesson.")[1])
            x_data = li.get('x-data', '{}')
            status_concluida = "finished:true" in x_data.replace(" ", "").replace("\n", "")
            aulas.append({'id': lesson_id, 'concluida': status_concluida})
        except (ValueError, IndexError):
            continue
    return aulas

# --- Funções de Chamada de API ---

def chamar_learning_center_init(session, csrf_token, link_curso):
    """Carrega a página e chama o método 'init' para obter o HTML completo do curso."""
    print("  ➡️  Carregando estrutura do curso (chamada init)...")
    try:
        resp_curso_inicial = session.get(link_curso, timeout=60)
        resp_curso_inicial.raise_for_status()
        soup_curso = BeautifulSoup(resp_curso_inicial.text, 'html.parser')
        div_principal = soup_curso.find("div", attrs={"wire:initial-data": True})
        if not div_principal: return None
        dados_raw = html_parser.unescape(div_principal['wire:initial-data'])
        dados_learning_center = json.loads(dados_raw)
        payload = {"fingerprint": dados_learning_center['fingerprint'], "serverMemo": dados_learning_center['serverMemo'], "updates": [{"type": "callMethod", "payload": {"id": dados_learning_center['fingerprint']['id'], "method": "init", "params": []}}]}
        headers = {"accept": "application/json", "content-type": "application/json", "x-csrf-token": csrf_token, "x-livewire": "true", "Referer": link_curso, "User-Agent": "Mozilla/5.0"}
        url = "https://jornadadedados.alpaclass.com/livewire/message/v2.portal.learning-center"
        resp = session.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        print(f"  ✅ [INIT] Status: {resp.status_code}")
        return resp.json().get('effects', {}).get('html', '')
    except Exception as e:
        print(f"  ❌ Erro na chamada 'init': {e}")
        return None

def chamar_course_module_card_e_pegar_aulas(session, csrf_token, dados_componente_card, link_curso):
    """Chama a API do módulo e retorna uma lista de aulas com ID e status."""
    payload = {"fingerprint": dados_componente_card['fingerprint'], "serverMemo": dados_componente_card['serverMemo'], "updates": [{"type": "callMethod", "payload": {"id": dados_componente_card['fingerprint']['id'], "method": "loadLessons", "params": []}}, {"type": "callMethod", "payload": {"id": dados_componente_card['fingerprint']['id'], "method": "$set", "params": ["expanded", True]}}]}
    headers = {"accept": "application/json", "content-type": "application/json", "x-csrf-token": csrf_token, "x-livewire": "true", "Referer": link_curso, "User-Agent": "Mozilla/5.0"}
    url = "https://jornadadedados.alpaclass.com/livewire/message/v2.portal.course-module-card"
    try:
        resp = session.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        html_resposta = resp.json().get('effects', {}).get('html', '')
        return extrair_aulas_com_status(html_resposta)
    except requests.exceptions.RequestException:
        return []

def buscar_detalhes_completos_aula(session, csrf_token, dados_lesson_component, link_curso, lesson_id):
    """Chama a API active-lesson-component para pegar todos os detalhes, incluindo o slug."""
    if not dados_lesson_component: return None
    payload = {"fingerprint": dados_lesson_component['fingerprint'], "serverMemo": dados_lesson_component['serverMemo'], "updates": [{"type": "callMethod", "payload": {"id": dados_lesson_component['fingerprint']['id'], "method": "loadLesson", "params": [int(lesson_id)]}}]}
    headers = {"accept": "application/json", "content-type": "application/json", "x-csrf-token": csrf_token, "x-livewire": "true", "Referer": link_curso, "User-Agent": "Mozilla/5.0"}
    url = "https://jornadadedados.alpaclass.com/livewire/message/v2.portal.active-lesson-component"
    try:
        resp = session.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        js = resp.json()
        for emit in js.get('effects', {}).get('emits', []):
            if emit.get('event') == 'setActiveLesson':
                return emit['params'][0]
        return None
    except requests.exceptions.RequestException:
        return None

# --- Funções de Orquestração ---
def raspar_pagina_de_conteudos(session, log_area):
    log_area.text("➡️ Lendo a página principal de conteúdos...")
    url_conteudos = "https://jornadadedados.alpaclass.com/s/conteudos"
    try:
        response = session.get(url_conteudos)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        trilhas = {}
        h4_tags = soup.find_all('h4', id=lambda x: x and x.startswith('category-title-'))
        for h4 in h4_tags:
            nome_trilha = h4.text.strip()
            cursos_na_trilha = {}
            container_cursos = h4.find_parent('div').find_parent('div').find_next_sibling('div')
            if not container_cursos: continue
            for a_tag in container_cursos.find_all('a', href=lambda x: x and '/c/cursos/' in x):
                img_tag = a_tag.find('img')
                if img_tag and img_tag.has_attr('alt'):
                    nome_curso = img_tag['alt'].strip()
                    link_curso = a_tag['href']
                    cursos_na_trilha[nome_curso] = link_curso
            if cursos_na_trilha:
                trilhas[nome_trilha] = cursos_na_trilha
        log_area.text(f"✅ Página de conteúdos lida! {len(trilhas)} trilhas encontradas.")
        return trilhas
    except requests.exceptions.RequestException as e:
        log_area.text(f"  ❌ Falha ao carregar a página de conteúdos: {e}")
        return {}

def raspar_curso(session, link_curso, log_area):
    """Função que usa concorrência para buscar slugs e status de forma rápida."""
    try:
        resp_curso_inicial = session.get(link_curso)
        resp_curso_inicial.raise_for_status()
        soup_curso = BeautifulSoup(resp_curso_inicial.text, 'html.parser')
        csrf_token = soup_curso.find('meta', {'name': 'csrf-token'})['content']
        
        html_real_do_curso = chamar_learning_center_init(session, csrf_token, link_curso)
        if not html_real_do_curso: return None
        
        soup_real = BeautifulSoup(html_real_do_curso, 'html.parser')
        dados_dos_modulos = extrair_componentes_modulos(html_real_do_curso)
        
        dados_lesson_component = None
        for div in soup_real.find_all("div", attrs={"wire:initial-data": True}):
            dados = json.loads(html_parser.unescape(div['wire:initial-data']))
            if dados.get('fingerprint', {}).get('name') == 'v2.portal.active-lesson-component':
                dados_lesson_component = dados
                break
        
        curso_data = {"aulas": []}
        if not dados_dos_modulos:
            log_area.text("  - Nenhum módulo encontrado nesta página.")
            return curso_data

        log_area.text(f"  - Encontrados {len(dados_dos_modulos)} módulos. Processando...")
        for dados_modulo in dados_dos_modulos:
            id_mod = dados_modulo.get('id_modulo')
            if not id_mod: continue
            
            aulas_com_status = chamar_course_module_card_e_pegar_aulas(session, csrf_token, dados_modulo, link_curso)
            if not aulas_com_status: continue

            log_area.text(f"    - Módulo {id_mod}: Buscando detalhes de {len(aulas_com_status)} aulas em paralelo...")
            
            status_map = {aula['id']: aula['concluida'] for aula in aulas_com_status}
            
            with ThreadPoolExecutor(max_workers=15) as executor:
                future_to_id = {executor.submit(buscar_detalhes_completos_aula, session, csrf_token, dados_lesson_component, link_curso, aula['id']): aula['id'] for aula in aulas_com_status}
                for future in as_completed(future_to_id):
                    detalhes_aula = future.result()
                    if detalhes_aula:
                        aula_id = detalhes_aula.get('id')
                        detalhes_aula['concluida'] = status_map.get(aula_id, False)
                        curso_data["aulas"].append(detalhes_aula)
        return curso_data
    except Exception as e:
        log_area.text(f"  ❌ Erro geral ao raspar o curso {link_curso}: {e}")
        return None

def run_full_scraper(session, log_area):
    """Função principal que orquestra todo o scraping."""
    trilhas_e_cursos = raspar_pagina_de_conteudos(session, log_area)
    if not trilhas_e_cursos:
        log_area.error("Nenhuma trilha ou curso encontrado. Encerrando.")
        return None

    lista_de_aulas = []
    total_cursos = sum(len(c) for c in trilhas_e_cursos.values())
    cursos_processados = 0

    log_area.text("\n--- ETAPA 2: Iniciando a raspagem de cada curso ---")
    for nome_trilha, cursos in trilhas_e_cursos.items():
        log_area.text(f"\nTrabalhando na Trilha: '{nome_trilha}'")
        
        for nome_curso, link_curso in cursos.items():
            cursos_processados += 1
            log_area.text(f"  ({cursos_processados}/{total_cursos}) Raspando o curso: '{nome_curso}'")
            
            dados_do_curso = raspar_curso(session, link_curso, log_area)
            
            if dados_do_curso and dados_do_curso.get("aulas"):
                for aula in dados_do_curso["aulas"]:
                    slug_da_aula = aula.get('slug')
                    link_da_aula = f"{link_curso.split('?')[0]}?lessonSlug={slug_da_aula}" if slug_da_aula else None
                    linha = {
                        'trilha_nome': nome_trilha,
                        'curso_nome': nome_curso,
                        'curso_link': link_curso,
                        'modulo_id': aula.get('module_id'),
                        'modulo_nome': aula.get('module', {}).get('name'),
                        'aula_id': aula.get('id'),
                        'aula_nome': aula.get('name'),
                        'aula_slug': slug_da_aula,
                        'aula_link': link_da_aula,
                        'aula_concluida': aula.get('concluida', False),
                        'aula_sumario': aula.get('summary'),
                        'aula_conteudo_html': aula.get('html_content')
                    }
                    lista_de_aulas.append(linha)
            else:
                linha = {
                    'trilha_nome': nome_trilha, 'curso_nome': nome_curso, 'curso_link': link_curso,
                    'modulo_id': None, 'modulo_nome': 'N/A', 'aula_id': None,
                    'aula_nome': 'N/A', 'aula_slug': None, 'aula_link': None,
                    'aula_concluida': None,
                    'aula_sumario': None,
                    'aula_conteudo_html': None
                }
                lista_de_aulas.append(linha)

            time.sleep(1)

    if lista_de_aulas:
        return pd.DataFrame(lista_de_aulas)
    return pd.DataFrame()

