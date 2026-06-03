import requests
from bs4 import BeautifulSoup

url = "https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=9612&palavraChave=cfop%20exterior&modulosSelecionados=0&intencaoID=0"
headers = {
    'User-Agent': 'Mozilla/5.0'
}
r = requests.get(url, headers=headers, verify=False, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')
text = soup.get_text(separator='\n', strip=True)

with open('solucao_final.txt', 'w', encoding='utf-8') as f:
    f.write(text)
