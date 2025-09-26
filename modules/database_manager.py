# modules/database_manager.py

import sqlite3
import pandas as pd
import os

DB_PATH = 'dados/jornada_data.db'

def init_db():
    """
    Inicializa o banco de dados e cria as tabelas 'cursos' e 'plano_estudos'
    se elas não existirem.
    """
    os.makedirs('dados', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela para armazenar todos os dados raspados da plataforma
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos (
        trilha_nome TEXT,
        curso_nome TEXT,
        curso_link TEXT,
        modulo_id INTEGER,
        modulo_nome TEXT,
        aula_id INTEGER PRIMARY KEY,
        aula_nome TEXT,
        aula_slug TEXT,
        aula_link TEXT,
        aula_concluida BOOLEAN,
        aula_sumario TEXT,
        aula_conteudo_html TEXT
    )
    ''')

    # Tabela para o plano de estudos do usuário
    # Adicionamos colunas que serão preenchidas pelo data_joiner
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plano_estudos (
        "Trilha" TEXT,
        "Módulo" TEXT,
        "Carga Horária (h)" REAL,
        "aula_link" TEXT,
        "aula_concluida" BOOLEAN
    )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso.")

def save_df_to_db(df, table_name):
    """
    Salva um DataFrame em uma tabela do banco de dados, substituindo a tabela existente.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")
        return False

def load_table_to_df(table_name):
    """
    Carrega uma tabela do banco de dados para um DataFrame do Pandas.
    Retorna um DataFrame vazio se a tabela não existir.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
        
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except pd.io.sql.DatabaseError:
        # Retorna um DF vazio se a tabela não for encontrada
        return pd.DataFrame()

def table_exists_and_has_data(table_name):
    """
    Verifica se uma tabela existe e contém pelo menos uma linha.
    """
    df = load_table_to_df(table_name)
    return not df.empty