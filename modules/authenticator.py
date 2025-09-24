import requests
from bs4 import BeautifulSoup

def autenticar_jornadadedados(email, senha):
    LOGIN_URL = "https://jornadadedados.alpaclass.com/s/login"
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    try:
        response_get = session.get(LOGIN_URL)
        response_get.raise_for_status()
        soup = BeautifulSoup(response_get.text, 'html.parser')
        meta_tag = soup.find('meta', {'name': 'csrf-token'})
        if not meta_tag:
            return None
        csrf_token = meta_tag['content']
        login_data = {"_token": csrf_token, "email": email, "password": senha}
        response_post = session.post(LOGIN_URL, data=login_data, headers={'Referer': LOGIN_URL})
        response_post.raise_for_status()
        if "/conteudos" in response_post.url:
            return session
        else:
            return None
    except requests.RequestException:
        return None