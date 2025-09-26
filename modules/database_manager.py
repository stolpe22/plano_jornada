# modules/database_manager.py

import sqlite3
import pandas as pd
import os
import re
from bs4 import BeautifulSoup

DB_PATH = 'dados/jornada_data.db'

def init_db():
    """
    Inicializa o banco de dados e cria as tabelas, incluindo a tabela virtual FTS5 e os gatilhos de sincronização.
    """
    os.makedirs('dados', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos (
        trilha_nome TEXT, curso_nome TEXT, curso_link TEXT, modulo_id INTEGER,
        modulo_nome TEXT, aula_id INTEGER PRIMARY KEY, aula_nome TEXT, aula_slug TEXT,
        aula_link TEXT, aula_concluida BOOLEAN, aula_sumario TEXT, aula_conteudo_html TEXT
    )
    ''')

    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS cursos_fts USING fts5(
        trilha_nome, curso_nome, modulo_nome, aula_nome, aula_sumario, aula_conteudo,
        content='cursos', content_rowid='aula_id', tokenize = 'unicode61'
    )
    ''')

    cursor.executescript('''
    CREATE TRIGGER IF NOT EXISTS cursos_ai AFTER INSERT ON cursos BEGIN
      INSERT INTO cursos_fts(rowid, trilha_nome, curso_nome, modulo_nome, aula_nome, aula_sumario, aula_conteudo)
      VALUES (new.aula_id, new.trilha_nome, new.curso_nome, new.modulo_nome, new.aula_nome, new.aula_sumario, new.aula_conteudo_html);
    END;
    CREATE TRIGGER IF NOT EXISTS cursos_ad AFTER DELETE ON cursos BEGIN
      INSERT INTO cursos_fts(cursos_fts, rowid, trilha_nome, curso_nome, modulo_nome, aula_nome, aula_sumario, aula_conteudo)
      VALUES ('delete', old.aula_id, old.trilha_nome, old.curso_nome, old.modulo_nome, old.aula_nome, old.aula_sumario, old.aula_conteudo_html);
    END;
    CREATE TRIGGER IF NOT EXISTS cursos_au AFTER UPDATE ON cursos BEGIN
      INSERT INTO cursos_fts(cursos_fts, rowid, trilha_nome, curso_nome, modulo_nome, aula_nome, aula_sumario, aula_conteudo)
      VALUES ('delete', old.aula_id, old.trilha_nome, old.curso_nome, old.modulo_nome, old.aula_nome, old.aula_sumario, old.aula_conteudo_html);
      INSERT INTO cursos_fts(rowid, trilha_nome, curso_nome, modulo_nome, aula_nome, aula_sumario, aula_conteudo)
      VALUES (new.aula_id, new.trilha_nome, new.curso_nome, new.modulo_nome, new.aula_nome, new.aula_sumario, new.aula_conteudo_html);
    END;
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plano_estudos (
        "Trilha" TEXT, "Módulo" TEXT, "Carga Horária (h)" REAL, 
        "aula_link" TEXT, "aula_concluida" BOOLEAN
    )''')

    conn.commit()
    conn.close()

def save_df_to_db(df, table_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        if table_name == 'cursos':
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cursos")
            conn.commit()
            
            if 'aula_conteudo_html' in df.columns:
                 df['aula_conteudo_html'] = df['aula_conteudo_html'].fillna('').apply(
                     lambda x: BeautifulSoup(x, 'html.parser').get_text(separator=' ', strip=True)
                 )
            df.to_sql(table_name, conn, if_exists='append', index=False)
        else:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")
        return False

def search_courses(query):
    conn = sqlite3.connect(DB_PATH)
    sql_query = """
    SELECT c.*, fts.rank
    FROM cursos AS c
    JOIN cursos_fts AS fts ON c.aula_id = fts.rowid
    WHERE fts.cursos_fts MATCH ?
    ORDER BY fts.rank;
    """
    sanitized_query = re.sub(r'[^a-zA-Z0-9\s\u00C0-\u017F]', '', query, re.UNICODE).strip()
    if not sanitized_query:
        conn.close()
        return pd.DataFrame()
    fts_query = ' '.join([f'{term}*' for term in sanitized_query.split()])
    df = pd.read_sql_query(sql_query, conn, params=(fts_query,))
    conn.close()
    return df

def load_table_to_df(table_name):
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except pd.io.sql.DatabaseError:
        return pd.DataFrame()

def table_exists_and_has_data(table_name):
    df = load_table_to_df(table_name)
    return not df.empty