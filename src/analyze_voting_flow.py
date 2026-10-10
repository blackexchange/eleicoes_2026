"""
Módulo de Auditoria e Análise de Fluxo de Votação por Minuto a partir de logs da urna (.logjez / logd.dat).
Alta performance com streaming sequencial do ZIP e parsing concorrente multithread.
"""

import argparse
import concurrent.futures
import io
import os
import re
import sys
import time
import zipfile
from datetime import datetime
import pandas as pd
import duckdb

sys.stdout.reconfigure(line_buffering=True)


def parse_jez_fast(jez_name: str, zip_bytes: bytes, uf: str):
    """Extrai e calcula as métricas eleitorais de um log individual de urna."""
    m_file = re.search(r"([a-z]{2})(\d{5})(\d{4})(\d{4})-log\.jez", jez_name, re.IGNORECASE)
    if not m_file:
        return None
    _, cod_mun, zona_str, secao_str = m_file.groups()
    zona, secao = int(zona_str), int(secao_str)

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as jz:
            text = jz.read("logd.dat").decode("latin1", errors="replace")
    except Exception:
        return None

    # Identificar modelo de hardware
    lib_match = re.search(r"avusrlib(ue20\d{2})", text, re.IGNORECASE)
    if lib_match:
        modelo = lib_match.group(1).upper()
    else:
        m_match = re.search(r"Modelo da Urna:\s*(UE20\d{2})", text, re.IGNORECASE)
        if m_match:
            modelo = m_match.group(1).upper()
        else:
            m_alt = re.search(r"\b(UE20\d{2})\b", text)
            modelo = m_alt.group(1).upper() if m_alt else "DESCONHECIDO"

    # Eventos de votação do dia 04/10/2026
    current_hab = None
    voter_count = 0
    durations = []
    first_vote = None
    last_vote = None

    for line in text.splitlines():
        if not line.startswith("04/10/2026"):
            continue
        parts = line.split("\t")
        if len(parts) >= 5:
            dt_str, msg = parts[0], parts[4].lower()
            if "eleitor foi habilitado" in msg or "tipo de habilita" in msg:
                if current_hab is None:
                    try:
                        current_hab = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                    except Exception:
                        pass
            elif "o voto do eleitor foi computado" in msg or "voto confirmado para [presidente]" in msg:
                if current_hab is not None:
                    try:
                        dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                        dur_sec = (dt - current_hab).total_seconds()
                        if 3 <= dur_sec <= 900:
                            durations.append(dur_sec)
                            voter_count += 1
                            if first_vote is None:
                                first_vote = current_hab
                            last_vote = dt
                    except Exception:
                        pass
                    current_hab = None

    if voter_count > 0 and first_vote and last_vote:
        span_min = max(1.0, (last_vote - first_vote).total_seconds() / 60.0)
        avg_dur = sum(durations) / len(durations)
        med_dur = float(pd.Series(durations).median())
        min_dur = float(min(durations))
        max_dur = float(max(durations))

        return {
            "uf": uf.upper(),
            "cod_municipio": cod_mun,
            "zona": zona,
            "secao": secao,
            "modelo_urna": modelo,
            "total_eleitores_votaram": voter_count,
            "primeiro_voto": first_vote.strftime("%H:%M:%S"),
            "ultimo_voto": last_vote.strftime("%H:%M:%S"),
            "duracao_sessao_min": round(span_min, 1),
            "votos_por_minuto": round(voter_count / span_min, 3),
            "tempo_medio_segundos": round(avg_dur, 1),
            "tempo_medio_minutos": round(avg_dur / 60.0, 2),
            "tempo_mediano_segundos": round(med_dur, 1),
            "tempo_min_segundos": round(min_dur, 1),
            "tempo_max_segundos": round(max_dur, 1)
        }
    return None


def analyze_uf_logs(uf: str = "BA", ano: int = 2026, turno: int = 1, batch_workers: int = 8, output_dir: str = "data/processed"):
    os.makedirs(output_dir, exist_ok=True)
    uf = uf.upper()
    zip_path = f"data/logs/bu_imgbu_logjez_rdv_vscmr_{ano}_{turno}t_{uf}.zip"

    if not os.path.exists(zip_path):
        print(f"Erro: Arquivo {zip_path} não encontrado.")
        return None

    print(f"=== INICIANDO AUDITORIA DOS LOGS OFICIAIS DE {uf} ({ano} - {turno}º TURNO) ===", flush=True)
    t_start = time.time()

    results = []

    with zipfile.ZipFile(zip_path, "r") as z:
        jez_infos = [info for info in z.infolist() if info.filename.endswith(".jez")]
        total_files = len(jez_infos)
        print(f"Total de urnas a processar: {total_files}", flush=True)

        batch_size = 500
        total_batches = (total_files + batch_size - 1) // batch_size

        for b_idx in range(total_batches):
            batch_slice = jez_infos[b_idx * batch_size : (b_idx + 1) * batch_size]
            batch_data = [(info.filename, z.read(info)) for info in batch_slice]

            # Processa o lote em paralelo na memória
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_workers) as executor:
                futures = [executor.submit(parse_jez_fast, fn, raw, uf) for fn, raw in batch_data]
                for f in concurrent.futures.as_completed(futures):
                    res = f.result()
                    if res:
                        results.append(res)

            done_count = min(total_files, (b_idx + 1) * batch_size)
            elapsed = time.time() - t_start
            rate = done_count / max(0.1, elapsed)
            pct = done_count / total_files * 100
            print(f"Progresso: {done_count}/{total_files} ({pct:.1f}%) | Velocidade: {rate:.1f} urnas/s | Válidas: {len(results)}", flush=True)

    df_res = pd.DataFrame(results)
    total_time = time.time() - t_start
    print(f"\n[OK] Auditoria concluída em {total_time:.1f}s: {len(df_res)} seções eleitorais auditadas.", flush=True)

    # Exportar para CSV e DuckDB
    csv_path = os.path.join(output_dir, f"fluxo_votacao_urnas_{uf}_{ano}.csv")
    df_res.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"[OK] Arquivo CSV exportado: {csv_path}", flush=True)

    duckdb_path = os.path.join(output_dir, "eleicoes.duckdb")
    con = duckdb.connect(duckdb_path)
    table_name = f"fluxo_votacao_urnas_{uf}_{ano}"
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_res")
    print(f"[OK] Tabela {table_name} criada no DuckDB: {duckdb_path}", flush=True)

    return df_res


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auditoria de Fluxo de Votação por Urna (LOGJEZ).")
    parser.add_argument("--uf", type=str, default="BA", help="UF a processar (ex: BA, RR, SP)")
    parser.add_argument("--ano", type=int, default=2026, help="Ano da eleição")
    parser.add_argument("--turno", type=int, default=1, help="Turno da eleição")
    parser.add_argument("--workers", type=int, default=8, help="Número de threads por lote")
    args = parser.parse_args()

    analyze_uf_logs(uf=args.uf, ano=args.ano, turno=args.turno, batch_workers=args.workers)
