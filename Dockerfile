# Dockerfile

# 1. imagem base oficial do Python. A versão 'slim' é mais leve.
FROM python:3.11-slim

# 2. diretório de trabalho dentro do container.
WORKDIR /app

# 3. arquivo de requisitos primeiro. Isso otimiza o cache do Docker.
COPY requirements.txt .

# 4. bibliotecas Python.
RUN pip install --no-cache-dir -r requirements.txt

# 5. todo o resto do código do projeto para dentro do container.
COPY . .

# 6. porta que o Streamlit usa, para acessá-la de fora.
EXPOSE 8501

# 7. comando para iniciar o aplicativo quando o container rodar.
# O '--server.address=0.0.0.0' é crucial para que o app seja acessível fora do container.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.serverAddress=localhost"]