import urllib.request
import gzip
import json
import duckdb
import os

def fetch_income_data():
    os.makedirs("data/geo", exist_ok=True)
    
    # Lista de municípios da Bahia
    with open("data/geo/ibge_municipios_ba.json", "r", encoding="utf-8") as f:
        ibge_munis = json.load(f)
    
    muni_ids = [str(m["id"]) for m in ibge_munis]
    print(f"Buscando dados de renda/salário para {len(muni_ids)} municípios da Bahia...")

    # Indicadores oficiais IBGE Cidades:
    # 29168: Salário médio mensal dos trabalhadores formais (em salários mínimos)
    # 29171: PIB per capita a preços correntes (R$)
    # 29169: Pessoal ocupado total
    
    # Consultar API IBGE em blocos de municípios
    # Endpoint: https://servicodados.ibge.gov.br/api/v1/pesquisas/indicadores/29168|29171/resultados/{municipios}
    
    chunk_size = 50
    results_map = {}
    
    for i in range(0, len(muni_ids), chunk_size):
        chunk = muni_ids[i:i+chunk_size]
        ids_str = "|".join(chunk)
        url = f"https://servicodados.ibge.gov.br/api/v1/pesquisas/indicadores/29168|29171/resultados/{ids_str}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                try:
                    content = gzip.decompress(raw).decode("utf-8")
                except Exception:
                    content = raw.decode("utf-8")
                data = json.loads(content)
                
                for item in data:
                    ind_id = str(item.get("id"))
                    res_list = item.get("res", [])
                    for res in res_list:
                        m_code = str(res.get("municipio", {}).get("id") or res.get("localidade"))
                        res_val = res.get("res", {})
                        if res_val:
                            last_year = sorted(res_val.keys())[-1]
                            val_str = res_val[last_year]
                            try:
                                val_num = float(val_str.replace(",", ".")) if val_str and val_str != "-" else 0.0
                            except:
                                val_num = 0.0
                            
                            if m_code not in results_map:
                                results_map[m_code] = {}
                            
                            if ind_id == "29168":
                                results_map[m_code]["SALARIO_MEDIO_SM"] = val_num
                            elif ind_id == "29171":
                                results_map[m_code]["PIB_PER_CAPITA"] = val_num
        except Exception as e:
            print(f"Aviso no lote {i}: {e}")
            
    print(f"Total municípios com dados de renda/salário obtidos: {len(results_map)}/417")
    
    with open("data/geo/renda_municipios_ba.json", "w", encoding="utf-8") as f:
        json.dump(results_map, f)
        
    return results_map

if __name__ == "__main__":
    fetch_income_data()
