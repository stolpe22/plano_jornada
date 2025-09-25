# Scraper e Enriquecedor de Plano de Estudos da Jornada de Dados

Este projeto é uma aplicação web construída com **Streamlit** que automatiza duas tarefas principais:

- **Web Scraping:** Autentica-se na plataforma Jornada de Dados e extrai uma lista completa de todas as trilhas, cursos, módulos e aulas disponíveis, incluindo o slug para gerar links diretos e o status de conclusão de cada aula.
- **Enriquecimento de Dados:** Utiliza um arquivo CSV com um plano de estudos fornecido pelo usuário e, através de correspondência difusa (fuzzy matching), associa cada módulo do plano ao seu link correspondente e status de conclusão, exportando um novo CSV com os dados enriquecidos.
- **Exploração Interativa:** Permite filtrar, buscar e navegar de forma dinâmica por todo o conteúdo raspado, inclusive com busca fuzzy, filtragem por trilha e visualização de relevância dos resultados.

O objetivo é transformar um plano de estudos estático numa ferramenta de navegação dinâmica, facilitando o acesso direto ao conteúdo da plataforma e o acompanhamento do progresso.

---

## ✨ Funcionalidades

- **Interface Web Simples:** Uma interface amigável criada com Streamlit que guia o usuário pelo processo de scraping, junção de dados e exploração dos cursos.
- **Autenticação Segura:** O usuário insere suas credenciais, que são usadas para criar uma sessão autenticada para o scraping dos dados.
- **Scraping Concorrente:** Utiliza multithreading para acelerar o processo de busca pelos detalhes das aulas, fazendo múltiplas requisições em paralelo.
- **Status de Conclusão:** O scraper coleta o status de conclusão de cada aula diretamente da plataforma.
- **Junção Inteligente de Dados:** Emprega a biblioteca `thefuzz` para fazer a correspondência entre os nomes dos módulos/cursos no plano de estudos e os nomes extraídos da plataforma, mesmo que não sejam idênticos.
- **Dashboard e Busca Fuzzy:** Visualize seu progresso geral, filtre por trilha, busque por termos aproximados (inclusive com erros de digitação) e navegue diretamente para cada aula.
- **Relevância dos Resultados:** A busca mostra o score de relevância de cada resultado.
- **Exportação de Resultados:** Gera um arquivo CSV final com o plano de estudos original enriquecido com colunas de link da aula e status de conclusão.

---

## 📂 Estrutura do Projeto

```
PLANO_JORNADA/
│
├── dados/
│   ├── plano_de_estudos.csv              # INPUT: Seu plano de estudos.
│   ├── cursos_jornada.csv                # OUTPUT: Gerado pelo scraper.
│   ├── plano_de_estudos_com_links.csv    # OUTPUT: O resultado final com links e status.
│
├── modules/
│   ├── authenticator.py                  # Autenticação na plataforma.
│   ├── scraper.py                        # Lógica completa de scraping.
│   ├── data_joiner.py                    # Junção e enriquecimento dos dados via fuzzy matching.
│
├── pages/
│   ├── 1_scraper_page.py                 # Página Streamlit para scraping e junção.
│   ├── 2_dashboard_page.py               # Página Streamlit para visualização do progresso.
│   ├── 3_jornada_courses_page.py         # NOVA: Página Streamlit para exploração de cursos e busca fuzzy.
├── app.py                                # Página inicial da aplicação Streamlit.
├── requirements.txt                      # Lista de dependências do projeto.
├── README.md                             # Este arquivo.
├── .gitignore
```

---

## 🚀 Como Configurar e Executar

Siga os passos abaixo para executar o projeto localmente.

### 1. Pré-requisitos

- Python 3.8 ou superior.

### 2. Instalação

Clone este repositório e crie um ambiente virtual:

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar o ambiente virtual (Windows)
.venv\Scripts\activate

# Ativar o ambiente virtual (macOS/Linux)
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### 3. Preparar o Plano de Estudos

- Crie a pasta `dados` na raiz do projeto, caso não exista.
- Coloque o seu arquivo CSV de plano de estudos como `plano_de_estudos.csv` dentro da pasta `dados`.
- O CSV deve ter pelo menos as colunas **Trilha** e **Módulo** (ou equivalentes).

### 4. Executar a Aplicação

Com o ambiente virtual ativado, rode:

```bash
streamlit run app.py
```

A interface abrirá no navegador.

---

## 📖 Como Usar

A aplicação está dividida em várias páginas principais na barra lateral do Streamlit:

### 1. Scraper & Junção

- Insira seu e-mail e senha da plataforma Jornada de Dados.
- Clique em **"Fazer Scraping Agora"** para coletar todos os dados de cursos, módulos e aulas, incluindo links e status de conclusão.
- Após o scraping, clique em **"Gerar Links no Plano de Estudos"** para fazer a junção entre seu plano e os dados coletados, gerando o arquivo enriquecido `plano_de_estudos_com_links.csv`.

### 3. Dashboard Plano de Estudos

- Visualize seu progresso geral e por trilha.
- Veja métricas, barras de progresso e uma tabela interativa com links diretos para cada aula. É possível marcar aulas como concluídas diretamente pela interface.

### 3. Exploração dos Cursos (Busca Fuzzy)

- Acesse a página **"Explorador de Cursos da Jornada"**.
- Filtre por trilha, busque por termos (inclusive aproximados, com tolerância a erros de digitação), e ajuste a sensibilidade da busca fuzzy.
- Veja o score de relevância, acesse links diretos para as aulas, visualize sumário e conteúdo completo, e marque aulas como concluídas.
- A busca utiliza tanto correspondência por frase quanto por aproximação de palavra para garantir os melhores resultados.

---

## 🛠️ Tecnologias Utilizadas

- **Streamlit:** Interface web interativa.
- **Requests & BeautifulSoup4:** Comunicação HTTP e parsing do HTML.
- **Pandas:** Manipulação de dados e geração dos CSVs.
- **TheFuzz (FuzzyWuzzy):** Correspondência difusa de texto.
- **Concurrent.futures:** Multithreading para acelerar scraping.
- **Os, Json:** Utilidades para manipulação de arquivos e dados.

---

## 👨‍💻 Contribuição

Pull requests são bem-vindos! Sinta-se à vontade para abrir issues ou sugerir melhorias.

---

## 📎 Observações

- O scraper pode demorar alguns minutos, dependendo da quantidade de cursos e módulos.
- Certifique-se que seu plano está padronizado para melhores resultados na correspondência.
- O status de conclusão das aulas é extraído diretamente da plataforma, permitindo acompanhamento do progresso.
- A exploração dos cursos permite busca inteligente, útil para encontrar conteúdos mesmo com nomes não exatos ou erros comuns de digitação.

---