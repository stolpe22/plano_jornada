# Jornada Planner 🚀 – Scraper, Enriquecimento e Dashboard do Plano de Estudos

Uma solução interativa para transformar o plano de estudos do **Acelerador de Carreiras** da Jornada de Dados em uma ferramenta dinâmica e navegável, com links diretos para aulas, acompanhamento de progresso e busca inteligente por conteúdo.

---

## Sobre o Projeto

O acelerador de carreiras da Jornada de Dados oferece um plano de estudos personalizado em CSV, baseado nas respostas de um questionário. Este projeto foi criado para automatizar e facilitar o acesso ao conteúdo real da plataforma, conectando o plano às trilhas, cursos, módulos e aulas disponíveis, enriquecendo-o com links diretos e status de progresso.  
O sistema faz scraping autenticado, aplica correspondência difusa (fuzzy matching) para encontrar o melhor link de aula para cada item do plano, e oferece visualização, edição e acompanhamento do progresso em uma interface web moderna com **Streamlit**.

**Tudo acontece localmente:** os dados, progresso e credenciais são processados e armazenados apenas no seu computador, garantindo privacidade e performance.

---

## Principais Funcionalidades

- **Scraping Autenticado:** Extração automática de todas as trilhas, cursos, módulos e aulas da Jornada de Dados, incluindo links diretos para cada aula e status de conclusão.
- **Enriquecimento do Plano:** Correspondência inteligente (fuzzy match com `thefuzz`) entre o plano do acelerador (CSV) e os dados reais da plataforma, atribuindo o melhor link de aula possível a cada item.
- **Banco de Dados Local:** Todo o progresso e dados extraídos ficam em SQLite local (`dados/jornada_data.db`), permitindo buscas rápidas e persistência entre sessões.
- **Dashboard Visual:** Acompanhe o progresso total e por trilha, marque aulas como concluídas, edite e navegue pelo plano de estudos diretamente pela interface.
- **Busca Avançada nos Cursos:** Pesquise por qualquer termo (curso, módulo, tema, palavra-chave) usando busca textual inteligente (FTS5 no SQLite), filtrando por trilhas e visualizando relevância dos resultados.
- **Interface Web:** Navegação intuitiva por páginas (Scraper, Dashboard, Explorador de Cursos) via Streamlit.
- **Pronto para Docker:** Deploy simples e portátil em container Docker.

---

## Estrutura do Projeto

```
PLANO_JORNADA/
│
├── dados/
│   └── jornada_data.db                # Banco SQLite local (criado automaticamente)
│
├── modules/
│   ├── authenticator.py               # Login na plataforma Jornada de Dados
│   ├── data_joiner.py                 # Junção/enriquecimento do plano (fuzzy match)
│   ├── database_manager.py            # Operações de banco de dados e busca FTS
│   ├── scraper.py                     # Scraper principal dos cursos/módulos/aulas
│
├── pages/
│   ├── 1_scraper_page.py              # Página: Scraping e junção do plano
│   ├── 2_dashboard_page.py            # Página: Dashboard do plano de estudos
│   ├── 3_jornada_courses_page.py      # Página: Explorador dos cursos e busca avançada
│
├── app.py                            # Página inicial/menu principal
├── requirements.txt                   # Dependências Python
├── Dockerfile                         # Build e execução via Docker
├── .gitignore
├── README.md
```

---

## Instalação e Execução

### 1. Pré-requisitos

- **Python 3.8 ou superior** (recomenda-se Python 3.11)
- **pip** instalado
- **Git** para clonar o repositório

### 2. Clone o Repositório (Etapa Universal)

```bash
git clone https://github.com/stolpe22/plano_jornada.git
cd plano_jornada
```

### 3. Instalação por Sistema Operacional

#### **Windows**

1. **Crie e ative o ambiente virtual:**
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Instale as dependências:**
   ```cmd
   pip install -r requirements.txt
   ```

3. **Execute o app:**
   ```cmd
   streamlit run app.py
   ```
   O navegador abrirá automaticamente. Se não abrir, acesse [http://localhost:8501](http://localhost:8501).

---

#### **Linux / MacOS / WSL (Windows Subsystem for Linux)**

1. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o app:**
   ```bash
   streamlit run app.py
   ```
   O app estará disponível em [http://localhost:8501](http://localhost:8501).

---

## Execução com Docker (Opcional)

**Antes de iniciar, esteja no diretório raiz do projeto (`plano_jornada`).**

1. **Build da imagem:**
   ```bash
   docker build -t jornada-planner .
   ```

2. **Execute o container:**

   - **No Linux, MacOS ou WSL:**
     ```bash
     docker run -p 8501:8501 -v $(pwd)/dados:/app/dados jornada-planner
     ```

   - **No Windows (PowerShell):**
     ```powershell
     docker run -p 8501:8501 -v ${PWD}\dados:/app/dados jornada-planner
     ```

   - **No Windows (CMD):**
     ```cmd
     docker run -p 8501:8501 -v %cd%\dados:/app/dados jornada-planner
     ```

   O app estará disponível em [http://localhost:8501](http://localhost:8501).

---

## Fluxo e Como Usar

1. **Scraper e Junção**
   - Faça upload do CSV do seu plano (recebido pelo acelerador).
   - Insira suas credenciais da Jornada de Dados.
   - Execute o scraping da plataforma.
   - Gere os links/status para cada módulo/aula do seu plano.

2. **Dashboard**
   - Visualize seu progresso geral e por trilha.
   - Marque aulas como concluídas, edite o plano, navegue por links diretos.

3. **Cursos da Jornada**
   - Pesquise por palavra, frase ou tema.
   - Filtre por trilha.
   - Veja resultados ranqueados por relevância, acesse conteúdo e links.

**Todos os dados e edições são salvos automaticamente no banco local.**

---

## Tecnologias Utilizadas

- **Streamlit:** Interface web interativa e páginas
- **Requests + BeautifulSoup:** Scraping autenticado do HTML da plataforma
- **Pandas:** Manipulação e análise dos dados
- **TheFuzz:** Fuzzy matching para correspondência inteligente entre nomes
- **SQLite + FTS5:** Banco local rápido com busca textual avançada e persistência
- **Docker:** Deploy fácil e portátil para qualquer ambiente

---

## Observações Detalhadas

- Todo processamento ocorre **localmente**: credenciais, progresso e dados ficam só na sua máquina.
- O scraping pode levar alguns minutos, dependendo do volume de cursos/módulos no seu plano.
- A busca textual nos cursos usa FTS5 (Full Text Search) do SQLite, retornando resultados ranqueados por relevância.
- O dashboard permite edição e marcação interativa do progresso, com salvamento automático no banco.
- O plano enriquecido pode ser baixado como CSV, já com links e status de cada aula.

---

## Contribuição & Suporte

Sugestões, melhorias e pull requests são muito bem-vindos!  
Abra uma issue ou contribua diretamente pelo [repositório oficial](https://github.com/stolpe22/plano_jornada).

---