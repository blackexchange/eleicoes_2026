import urllib.request
import gzip
import json

def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
        if content[:2] == b'\x1f\x8b':
            content = gzip.decompress(content)
        return json.loads(content.decode('utf-8'))

data = get_json('https://servicodados.ibge.gov.br/api/v1/pesquisas/indicadores/all')
print(f"Total indicadores: {len(data)}")
for item in data:
    nome = item.get('indicador', '')
    for w in ['sal', 'rend', 'pib', 'sm']:
        if w in nome.lower():
            print(f"{item.get('id')}: {nome}")
            break
