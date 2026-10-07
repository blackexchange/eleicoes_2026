"""
Testes de ponta a ponta (E2E) e testes de métricas para o pipeline.
"""

import argparse
import io
import zipfile
from datetime import datetime
from pathlib import Path
import pytest
from src.metrics import UrnaMetricsAnalyzer
from src.parser import UrnaLogRecord
from src.pipeline import run_pipeline


@pytest.fixture
def realistic_log_records():
    return [
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 7, 0, 0), "INF", "00001", "Urna ligada"),
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 7, 5, 0), "INF", "00002", "Zeresima emitida"),
        # Eleitor 1: demora 45s (08:01:00 a 08:01:45)
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 8, 1, 0), "INF", "00020", "Eleitor habilitado por biometria"),
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 8, 1, 45), "INF", "00021", "O voto do eleitor foi computado"),
        # Eleitor 2: demora 60s (08:05:00 a 08:06:00)
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 8, 5, 0), "INF", "00020", "Eleitor habilitado"),
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 8, 6, 0), "INF", "00021", "Voto confirmado para todos os cargos"),
        # Eleitor 3: às 09:10:00 demorou 30s
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 9, 10, 0), "INF", "00020", "Eleitor habilitado"),
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 9, 10, 30), "INF", "00021", "Voto confirmado"),
        # Anomalia
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 10, 15, 0), "WAR", "00099", "Falha temporária de leitura biométrica"),
        # Encerramento
        UrnaLogRecord(2022, 1, "BA", "38490", 1, 42, datetime(2022, 10, 2, 17, 0, 0), "INF", "00030", "Encerramento da votação"),
    ]


def test_metrics_analyzer(realistic_log_records):
    times = UrnaMetricsAnalyzer.compute_voting_times(realistic_log_records)
    assert times["total_eleitores_processados"] == 3
    assert times["tempo_medio_segundos"] == 45.0  # (45 + 60 + 30) / 3 = 45.0
    assert times["tempo_min_segundos"] == 30.0
    assert times["tempo_max_segundos"] == 60.0

    hourly = UrnaMetricsAnalyzer.compute_hourly_traffic(realistic_log_records)
    assert hourly["08:00"] == 2
    assert hourly["09:00"] == 1
    assert hourly["10:00"] == 0

    anomalies = UrnaMetricsAnalyzer.detect_anomalies_and_restarts(realistic_log_records)
    assert len(anomalies) == 1
    assert "Falha temporária" in anomalies[0]["mensagem"]


@pytest.mark.asyncio
async def test_full_pipeline_e2e_with_local_logjez(tmp_path: Path):
    # Cria um arquivo .logjez sintético
    raw_log = """02/10/2022 07:00:00\tINF\t00001\tUrna ligada
02/10/2022 08:00:10\tINF\t00020\tEleitor habilitado
02/10/2022 08:00:50\tINF\t00021\tVoto confirmado
02/10/2022 17:00:00\tINF\t00030\tEncerramento da votação
"""
    logjez_path = tmp_path / "urna_test.logjez"
    with zipfile.ZipFile(logjez_path, "w") as zf:
        zf.writestr("logd.dat", raw_log.encode("utf-8"))

    output_dir = tmp_path / "processed"

    args = argparse.Namespace(
        ano=2022,
        turno=1,
        uf="BA",
        municipio="38490",
        zona=1,
        secao=1,
        file=str(logjez_path),
        format="all",
        output_dir=str(output_dir),
        no_metrics=False,
    )

    records = await run_pipeline(args)
    assert len(records) == 4
    assert (output_dir / "logs_2022_T1_BA.parquet").exists()
    assert (output_dir / "logs_2022_T1_BA.csv").exists()
    assert (output_dir / "eleicoes.duckdb").exists()
