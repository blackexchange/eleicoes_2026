"""
Pipeline de Download e Parsing em Lote de 1.000 Urnas Oficiais do TSE (2º Turno 2026 - Bahia).
Execução multi-threaded com conexão persistente e decoding em lote via Node.js V8.
"""

import json
import shutil
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import duckdb
import pandas as pd
import subprocess

# Configurações de diretórios
out_dir = Path("data/logs/2t_sample_1000")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Carrega as 1.000 chaves da amostra
keys_path = Path("scratch/sample_1000_keys.json")
with open(keys_path, "r", encoding="utf-8") as f:
    sample_keys = json.load(f)

print(f"Iniciando processamento para {len(sample_keys)} urnas...")

# Copia os 20 BUs já baixados anteriormente
prev_dir = Path("data/logs/2t_sample_20")
if prev_dir.exists():
    for f in prev_dir.glob("*-bu.dat"):
        shutil.copy(f, out_dir / f.name)
print(f"Arquivos pré-existentes copiados: {len(list(out_dir.glob('*-bu.dat')))}")

# 2. Função de Download Individual com Retry
base_url = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221/dados/ba"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def download_bu(item):
    cd_mun = item["cd_mun"]
    zona = str(item["zona"]).zfill(4)
    secao = str(item["secao"]).zfill(4)
    bu_name = f"o03221ba{cd_mun}{zona}{secao}-bu.dat"
    dest_path = out_dir / bu_name
    
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return item, True, "cached"
        
    aux_url = f"{base_url}/{cd_mun}/{zona}/{secao}/p003221-ba-m{cd_mun}-z{zona}-s{secao}-aux.json"
    
    for attempt in range(3):
        try:
            req_aux = urllib.request.Request(aux_url, headers=headers)
            with urllib.request.urlopen(req_aux, timeout=7) as r:
                aux_data = json.loads(r.read())
                hsh = aux_data["hashes"][0]["hash"]
                
            bu_url = f"{base_url}/{cd_mun}/{zona}/{secao}/{hsh}/{bu_name}"
            req_bu = urllib.request.Request(bu_url, headers=headers)
            with urllib.request.urlopen(req_bu, timeout=7) as r_bu:
                content = r_bu.read()
                dest_path.write_bytes(content)
                return item, True, "downloaded"
        except Exception as e:
            if attempt == 2:
                return item, False, str(e)
            time.sleep(0.3 * (attempt + 1))
            
    return item, False, "failed"

# 3. Execução Concorrente com ThreadPool
to_download = [item for item in sample_keys if not (out_dir / f"o03221ba{item['cd_mun']}{str(item['zona']).zfill(4)}{str(item['secao']).zfill(4)}-bu.dat").exists()]
print(f"Total de BUs a baixar da CDN do TSE: {len(to_download)}")

success_count = 0
fail_count = 0
t0 = time.time()

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(download_bu, item): item for item in to_download}
    for idx, fut in enumerate(as_completed(futures), 1):
        item, ok, status = fut.result()
        if ok:
            success_count += 1
        else:
            fail_count += 1
            print(f"  [ERRO] {item['mun_nome']} Z{item['zona']} S{item['secao']}: {status}")
            
        if idx % 100 == 0 or idx == len(to_download):
            elapsed = time.time() - t0
            print(f"Progresso: {idx}/{len(to_download)} baixados ({elapsed:.1f}s, {idx/elapsed:.1f} BUs/s)")

print(f"\nDownload concluído: {success_count} sucesso, {fail_count} falhas.")

# 4. Decodificação em Lote com Node.js
batch_json = Path("scratch/decoded_bu_1000_batch.json")
print("\nIniciando decodificação ASN.1 em lote com Node.js...")
t_dec0 = time.time()
cmd = ["node", "scratch/batch_decode_bu.js", str(out_dir), str(batch_json)]
p = subprocess.run(cmd, capture_output=True, text=True)
print("Saída do Node:", p.stdout.strip())
if p.returncode != 0:
    print("Erro no Node:", p.stderr)
    raise RuntimeError("Falha no decode batch Node.js")
print(f"Decodificação concluída em {time.time() - t_dec0:.2f}s!")

# 5. Carrega o mapa decodificado e junta com o 1º Turno do DuckDB
with open(batch_json, "r", encoding="utf-8") as f:
    decoded_bus = json.load(f)

print(f"Carregados {len(decoded_bus)} BUs decodificados. Integrando com dados do 1º Turno...")

con = duckdb.connect("data/processed/eleicoes.duckdb", read_only=True)
df_1t = con.execute("""
    SELECT 
        MUNICIPIO,
        ZONA,
        SECAO,
        LOCAL_VOTACAO,
        BAIRRO,
        MODELO_URNA,
        APTOS as APTOS_T1,
        COMPARECIMENTO as COMP_T1,
        ABSTENCAO as ABST_T1,
        PCT_ABSTENCAO as PCT_ABST_T1,
        QTD_BIOMETRIA as BIO_T1,
        QTD_MANUAL as MAN_T1,
        PCT_MANUAL as PCT_MAN_T1,
        VOTOS_13 as VOTOS_13_T1,
        VOTOS_22 as VOTOS_22_T1,
        PCT_VOTOS_13 as PCT_13_T1,
        PCT_VOTOS_22 as PCT_22_T1
    FROM auditoria_secoes_BA_2026;
""").df()

map_1t = {(row["ZONA"], row["SECAO"]): row.to_dict() for _, row in df_1t.iterrows()}

final_records = []
for item in sample_keys:
    zona = item["zona"]
    secao = item["secao"]
    cd_mun = item["cd_mun"]
    bu_key = f"o03221ba{cd_mun}{str(zona).zfill(4)}{str(secao).zfill(4)}-bu.dat"
    
    if bu_key not in decoded_bus:
        continue
        
    bu_data = decoded_bus[bu_key]
    conteudo = bu_data.get("conteudo", {}).get("entidadeBoletimUrna", {})
    
    # Comparecimento e Biometria 2T
    comp_2t = int(conteudo.get("qtdEleitoresCompareceram", {}).get("value", 0))
    det = conteudo.get("detalhamentoComparecimento", {})
    sem_bio_2t = int(det.get("qtdEleitoresCompareceramSemBiometria", {}).get("value", 0))
    bio_2t = int(det.get("qtdEleitoresHabilitadosPorBiometria", {}).get("value", 0))
    bio_graf_2t = int(det.get("qtdEleitoresHabilitadosPorBiografia", {}).get("value", 0))
    manual_2t = sem_bio_2t + bio_graf_2t
    
    # Resultados eleitorais 2T
    res_eleicao = conteudo.get("resultadosVotacaoPorEleicao", {}).get("content", [])
    aptos_2t = comp_2t
    votos_13_2t = 0
    votos_22_2t = 0
    brancos_2t = 0
    nulos_2t = 0
    
    for re_el in res_eleicao:
        if re_el.get("idEleicao", {}).get("value") == "6258": # Presidencial 2T
            aptos_2t = int(re_el.get("qtdEleitoresAptos", {}).get("value", comp_2t))
            tot_cargos = re_el.get("resultadosVotacao", {}).get("content", [])
            for tc in tot_cargos:
                for c in tc.get("totaisVotosCargo", {}).get("content", []):
                    for vv in c.get("votosVotaveis", {}).get("content", []):
                        qtd_v = int(vv.get("quantidadeVotos", {}).get("value", 0))
                        tp_voto = vv.get("tipoVoto", {}).get("valueDesc", "")
                        cod_cand = vv.get("identificacaoVotavel", {}).get("codigo", {}).get("value", "")
                        if cod_cand == "13":
                            votos_13_2t += qtd_v
                        elif cod_cand == "22":
                            votos_22_2t += qtd_v
                        elif tp_voto == "branco":
                            brancos_2t += qtd_v
                        elif tp_voto == "nulo":
                            nulos_2t += qtd_v

    abstencao_2t = max(0, aptos_2t - comp_2t)
    pct_abst_2t = round((abstencao_2t / aptos_2t * 100), 2) if aptos_2t > 0 else 0.0
    pct_man_2t = round((manual_2t / comp_2t * 100), 2) if comp_2t > 0 else 0.0
    validos_2t = votos_13_2t + votos_22_2t
    pct_13_2t = round((votos_13_2t / validos_2t * 100), 2) if validos_2t > 0 else 0.0
    pct_22_2t = round((votos_22_2t / validos_2t * 100), 2) if validos_2t > 0 else 0.0

    # Dados 1T
    row_1t = map_1t.get((zona, secao), {})
    comp_1t = int(row_1t.get("COMP_T1", 0))
    abst_1t = int(row_1t.get("ABST_T1", 0))
    pct_abst_1t = float(row_1t.get("PCT_ABST_T1", 0.0))
    man_1t = int(row_1t.get("MAN_T1", 0))
    bio_1t = int(row_1t.get("BIO_T1", 0))
    pct_man_1t = float(row_1t.get("PCT_MAN_T1", 0.0))
    votos_13_1t = int(row_1t.get("VOTOS_13_T1", 0))
    votos_22_1t = int(row_1t.get("VOTOS_22_T1", 0))
    pct_13_1t = float(row_1t.get("PCT_13_T1", 0.0))
    pct_22_1t = float(row_1t.get("PCT_22_T1", 0.0))

    rec = {
        "MUNICIPIO": item["mun_nome"],
        "ZONA": zona,
        "SECAO": secao,
        "COD_MUNICIPIO": cd_mun,
        "LOCAL_VOTACAO": row_1t.get("LOCAL_VOTACAO", "LOCAL ELEITORAL"),
        "BAIRRO": row_1t.get("BAIRRO", ""),
        "MODELO_URNA": item["modelo"],
        
        # 1T
        "1T_APTOS": comp_1t + abst_1t,
        "1T_COMPARECIMENTO": comp_1t,
        "1T_ABSTENCAO": abst_1t,
        "1T_PCT_ABSTENCAO": pct_abst_1t,
        "1T_QTD_BIOMETRIA": bio_1t,
        "1T_QTD_MANUAL": man_1t,
        "1T_PCT_MANUAL": pct_man_1t,
        "1T_VOTOS_13": votos_13_1t,
        "1T_VOTOS_22": votos_22_1t,
        "1T_PCT_13": pct_13_1t,
        "1T_PCT_22": pct_22_1t,
        
        # 2T (100% Oficial TSE)
        "2T_APTOS": aptos_2t,
        "2T_COMPARECIMENTO": comp_2t,
        "2T_ABSTENCAO": abstencao_2t,
        "2T_PCT_ABSTENCAO": pct_abst_2t,
        "2T_QTD_BIOMETRIA": bio_2t,
        "2T_QTD_MANUAL": manual_2t,
        "2T_PCT_MANUAL": pct_man_2t,
        "2T_VOTOS_13": votos_13_2t,
        "2T_VOTOS_22": votos_22_2t,
        "2T_BRANCOS": brancos_2t,
        "2T_NULOS": nulos_2t,
        "2T_PCT_13": pct_13_2t,
        "2T_PCT_22": pct_22_2t,
        
        # Deltas
        "DELTA_MANUAL": manual_2t - man_1t,
        "DELTA_PCT_MANUAL": round(pct_man_2t - pct_man_1t, 2),
        "DELTA_COMPARECIMENTO": comp_2t - comp_1t,
        "DELTA_ABSTENCAO": abstencao_2t - abst_1t,
        "DELTA_VOTOS_13": votos_13_2t - votos_13_1t,
        "DELTA_VOTOS_22": votos_22_2t - votos_22_1t
    }
    final_records.append(rec)

out_final = Path("data/processed/amostra_1000_urnas_auditoria_oficial.json")
with open(out_final, "w", encoding="utf-8") as f:
    json.dump(final_records, f, indent=2, ensure_ascii=False)

print(f"\n=======================================================")
print(f"Sucesso! {len(final_records)} urnas oficiais consolidadas.")
print(f"Arquivo gerado: {out_final.resolve()}")
print(f"=======================================================")
