# Scraper e Enriquecedor de Plano de Estudos da Jornada de Dados

Este projeto é uma aplicação web construída com **Streamlit** que automatiza duas tarefas principais:

- **Web Scraping:** Autentica-se na plataforma Jornada de Dados e extrai uma lista completa de todas as trilhas, cursos, módulos e aulas disponíveis, incluindo o slug para gerar links diretos.
- **Enriquecimento de Dados:** Utiliza um arquivo CSV com um plano de estudos fornecido pelo utilizador e, através de correspondência difusa (fuzzy matching), associa cada módulo do plano ao seu link correspondente, exportando um novo CSV com os dados enriquecidos.

O objetivo é transformar um plano de estudos estático numa ferramenta de navegação dinâmica, facilitando o acesso direto ao conteúdo da plataforma.

---

## ✨ Funcionalidades

- **Interface Web Simples:** Uma interface amigável criada com Streamlit que guia o utilizador através do processo.
- **Autenticação Segura:** O utilizador insere as suas credenciais, que são usadas para criar uma sessão autenticada para a raspagem dos dados.
- **Scraping Concorrente:** Utiliza multithreading para acelerar significativamente o processo de busca pelos detalhes das aulas, fazendo múltiplas requisições em paralelo.
- **Junção Inteligente de Dados:** Emprega a biblioteca thefuzz para fazer a correspondência entre os nomes dos módulos no plano de estudos e os nomes extraídos da plataforma, mesmo que não sejam idênticos.
- **Exportação de Resultados:** Gera um ficheiro CSV final com o plano de estudos original enriquecido com uma nova coluna contendo os links diretos para a primeira aula de cada módulo.

---

## 📂 Estrutura do Projeto

```
/
|
|--- dados/
|    |--- plano_de_estudos.csv              # INPUT: O seu plano de estudos.
|    |--- cursos_jornada.csv                # OUTPUT: Gerado pelo scraper.
|    |--- plano_de_estudos_com_links.csv    # OUTPUT: O resultado final.
|
|--- modules/
|    |--- authenticator.py                  # Lida com a autenticação na plataforma.
|    |--- scraper.py                        # Contém toda a lógica de web scraping.
|    |--- data_joiner.py                    # Contém a lógica para juntar os dados.
|
|--- app.py                                # Ficheiro principal da aplicação Streamlit.
|
|--- requirements.txt                      # Lista de dependências do projeto.
```

---

## 🚀 Como Configurar e Executar

Siga os passos abaixo para executar o projeto na sua máquina local.

### 1. Pré-requisitos

- Python 3.8 ou superior.

### 2. Instalação

Clone ou descarregue este repositório. Navegue até a pasta raiz do projeto e crie um ambiente virtual:

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar o ambiente virtual (Windows)
.venv\Scripts\activate

# Ativar o ambiente virtual (macOS/Linux)
source .venv/bin/activate
```

Instale as dependências listadas no requirements.txt:

```bash
pip install -r requirements.txt
```

### 3. Preparar o Plano de Estudos

- Crie a pasta `dados` na raiz do projeto, caso não exista.
- Dentro da pasta `dados`, coloque o seu ficheiro CSV com o plano de estudos e certifique-se de que o nome dele é `plano_de_estudos.csv`.
- A primeira linha do seu CSV deve ser o cabeçalho, contendo pelo menos as colunas **Trilha** e **Módulo**.

### 4. Executar a Aplicação

Com o ambiente virtual ativado, execute o seguinte comando no terminal, a partir da pasta raiz do projeto:

```bash
streamlit run app.py
```

O seu navegador abrirá automaticamente com a interface da aplicação.

---

## 📖 Como Usar

A interface é dividida em dois passos simples:

### 1. Fazer o Scraping

- Insira o seu e-mail e senha da plataforma Jornada de Dados.
- Clique no botão **"Fazer Scraping Agora"**.
- Aguarde o processo terminar. Pode acompanhar o progresso na área de log que aparecerá. Ao final, será criado o ficheiro `dados/cursos_jornada.csv`.

### 2. Gerar Links no Plano de Estudos

- Após o scraping ser concluído com sucesso, o botão **"Gerar Links no Plano de Estudos"** será habilitado.
- Clique nele para iniciar o processo de correspondência.
- Ao final, a aplicação exibirá uma amostra do resultado e disponibilizará um botão para descarregar o CSV final, `plano_de_estudos_com_links.csv`.

---

## 🛠️ Tecnologias Utilizadas

- **Streamlit:** Para a criação da interface web.
- **Requests & BeautifulSoup4:** Para a comunicação HTTP e parsing do HTML.
- **Pandas:** Para a manipulação dos dados e criação dos ficheiros CSV.
- **TheFuzz (FuzzyWuzzy):** Para a lógica de correspondência de texto difusa.
- **Concurrent.futures:** Para acelerar o scraping através de requisições paralelas (multithreading).

---

## 👨‍💻 Contribuição

Pull requests são bem-vindos! Sinta-se à vontade para abrir issues ou sugerir melhorias.

---