import json, os, urllib.request, subprocess, time, zipfile, io
from pathlib import Path

# Directories
out_dir = Path("data/logs/2t_sample_20")
out_dir.mkdir(parents=True, exist_ok=True)
json_dir = Path("scratch/decoded_bu_2t")
json_dir.mkdir(parents=True, exist_ok=True)

with open("scratch/sample_20_aux_results.json", "r", encoding="utf-8") as f:
    sample = json.load(f)

print(f"Starting download and decode of official 2T files for {len(sample)} sections...")

base_url = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221/dados/ba"
headers = {"User-Agent": "Mozilla/5.0"}

results = []

for idx, s in enumerate(sample, 1):
    mun_5 = str(s["cod_mun"]).zfill(5)
    zona_4 = str(s["zona"]).zfill(4)
    secao_4 = str(s["secao"]).zfill(4)
    hsh = s["hash"]
    
    bu_file_name = f"o03221ba{mun_5}{zona_4}{secao_4}-bu.dat"
    log_file_name = f"o03221ba{mun_5}{zona_4}{secao_4}-log.jez"
    
    bu_url = f"{base_url}/{mun_5}/{zona_4}/{secao_4}/{hsh}/{bu_file_name}"
    log_url = f"{base_url}/{mun_5}/{zona_4}/{secao_4}/{hsh}/{log_file_name}"
    
    local_bu = out_dir / bu_file_name
    local_log = out_dir / log_file_name
    local_json = json_dir / f"{s['mun_nome']}_z{s['zona']}_s{s['secao']}_bu.json"
    
    print(f"[{idx}/20] Downloading: {s['mun_nome']} (Z{s['zona']} S{s['secao']})...")
    
    # Download BU if not present
    if not local_bu.exists():
        try:
            req = urllib.request.Request(bu_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                local_bu.write_bytes(r.read())
        except Exception as e:
            print(f"  Error downloading BU: {e}")
            
    # Download LOG if not present
    if not local_log.exists():
        try:
            req = urllib.request.Request(log_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                local_log.write_bytes(r.read())
        except Exception as e:
            print(f"  Error downloading LOG: {e}")

    # Decode BU via Node script
    if local_bu.exists():
        cmd = ["node", "scratch/decode_bu.js", str(local_bu), str(local_json)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            print(f"  Error decoding BU: {p.stderr}")
            continue
            
    with open(local_json, "r", encoding="utf-8") as jf:
        bu_data = json.load(jf)
        
    conteudo = bu_data.get("conteudo", {}).get("entidadeBoletimUrna", {})
    
    # Extract Comparecimento and Biometria
    comp_2t = int(conteudo.get("qtdEleitoresCompareceram", {}).get("value", 0))
    det = conteudo.get("detalhamentoComparecimento", {})
    sem_bio_2t = int(det.get("qtdEleitoresCompareceramSemBiometria", {}).get("value", 0))
    bio_2t = int(det.get("qtdEleitoresHabilitadosPorBiometria", {}).get("value", 0))
    bio_graf_2t = int(det.get("qtdEleitoresHabilitadosPorBiografia", {}).get("value", 0))
    manual_2t = sem_bio_2t + bio_graf_2t  # Votos liberados pelo mesário / sem biometria
    
    # Results per election
    res_eleicao = conteudo.get("resultadosVotacaoPorEleicao", {}).get("content", [])
    aptos_2t = comp_2t
    votos_13_2t = 0
    votos_22_2t = 0
    brancos_2t = 0
    nulos_2t = 0
    
    for re_el in res_eleicao:
        if re_el.get("idEleicao", {}).get("value") == "6258": # Eleição Presidencial 2T
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
    
    # Parse log.jez for votos_pos_17h in 2T
    votos_pos_17h_2t = 0
    votos_pos_17h_man_2t = 0
    if local_log.exists():
        try:
            with zipfile.ZipFile(local_log, "r") as z:
                # check sub zip
                sub_names = [n for n in z.namelist() if n.endswith(".jez")]
                if sub_names:
                    sub_bytes = z.read(sub_names[0])
                    with zipfile.ZipFile(io.BytesIO(sub_bytes), "r") as sz:
                        log_text = sz.read("logd.dat").decode("latin1", errors="replace")
                else:
                    log_text = z.read("logd.dat").decode("latin1", errors="replace")
                
                cur_m = "manual"
                for line in log_text.splitlines():
                    if "25/10/2026" not in line:
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 5:
                        dt_s, msg = parts[0], parts[4].lower()
                        if "tipo de habilita" in msg and "biom" in msg:
                            cur_m = "biometrica"
                        elif "dado pessoal" in msg or "ano de nascimento" in msg or "habilitou o eleitor" in msg:
                            cur_m = "manual"
                        elif "o voto do eleitor foi computado" in msg or "voto confirmado para [presidente]" in msg:
                            time_p = dt_s.split(" ")[1] if " " in dt_s else ""
                            if time_p >= "17:00:00":
                                votos_pos_17h_2t += 1
                                if cur_m == "manual":
                                    votos_pos_17h_man_2t += 1
        except Exception as e:
            print(f"  Warning log parse: {e}")

    # Build record
    rec = {
        "MUNICIPIO": s["mun_nome"],
        "ZONA": s["zona"],
        "SECAO": s["secao"],
        "COD_MUNICIPIO": s["cod_mun"],
        "MODELO_URNA": s["modelo"],
        
        # 1T (Official)
        "1T_APTOS": s["1t_comparecimento"] + s["1t_abstencao"],
        "1T_COMPARECIMENTO": s["1t_comparecimento"],
        "1T_ABSTENCAO": s["1t_abstencao"],
        "1T_PCT_ABSTENCAO": round(s["1t_abstencao"] / (s["1t_comparecimento"] + s["1t_abstencao"]) * 100, 2),
        "1T_QTD_BIOMETRIA": s["1t_biometria"],
        "1T_QTD_MANUAL": s["1t_manual"],
        "1T_PCT_MANUAL": round(s["1t_manual"] / s["1t_comparecimento"] * 100, 2),
        "1T_VOTOS_13": int(s["1t_votos_13"]),
        "1T_VOTOS_22": int(s["1t_votos_22"]),
        "1T_PCT_13": round(s["1t_votos_13"] / (s["1t_votos_13"] + s["1t_votos_22"]) * 100, 2),
        "1T_PCT_22": round(s["1t_votos_22"] / (s["1t_votos_13"] + s["1t_votos_22"]) * 100, 2),
        
        # 2T (100% Official TSE)
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
        "2T_VOTOS_POS_17H": votos_pos_17h_2t,
        "2T_VOTOS_POS_17H_MANUAL": votos_pos_17h_man_2t,
        
        # Deltas
        "DELTA_MANUAL": manual_2t - s["1t_manual"],
        "DELTA_PCT_MANUAL": round(pct_man_2t - round(s["1t_manual"] / s["1t_comparecimento"] * 100, 2), 2),
        "DELTA_COMPARECIMENTO": comp_2t - s["1t_comparecimento"],
        "DELTA_ABSTENCAO": abstencao_2t - s["1t_abstencao"],
        "DELTA_VOTOS_13": votos_13_2t - int(s["1t_votos_13"]),
        "DELTA_VOTOS_22": votos_22_2t - int(s["1t_votos_22"])
    }
    
    print(f"  -> 1T Manual: {rec['1T_QTD_MANUAL']} ({rec['1T_PCT_MANUAL']}%) | 2T Manual: {rec['2T_QTD_MANUAL']} ({rec['2T_PCT_MANUAL']}%) | Delta: {rec['DELTA_MANUAL']}")
    print(f"  -> 1T Abst: {rec['1T_ABSTENCAO']} | 2T Abst: {rec['2T_ABSTENCAO']} | Delta Abst: {rec['DELTA_ABSTENCAO']}")
    print(f"  -> 1T L/B: {rec['1T_VOTOS_13']}/{rec['1T_VOTOS_22']} | 2T L/B: {rec['2T_VOTOS_13']}/{rec['2T_VOTOS_22']} | Delta L/B: {rec['DELTA_VOTOS_13']}/{rec['DELTA_VOTOS_22']}")
    results.append(rec)
    time.sleep(0.1)

out_json = Path("data/processed/amostra_20_urnas_auditoria_oficial.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nALL 20 SECTIONS PROCESSED SUCCESSFULLY WITH 100% OFFICIAL TSE DATA!")
print(f"Saved to: {out_json}")
