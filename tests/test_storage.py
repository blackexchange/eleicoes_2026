"""
Testes unitários para o módulo storage.py
"""

from datetime import datetime
from pathlib import Path
import duckdb
import pyarrow.parquet as pq
import pytest
from src.parser import UrnaLogRecord
from src.storage import UrnaStorage


@pytest.fixture
def sample_records():
    return [
        UrnaLogRecord(
            ano=2022,
            turno=1,
            uf="BA",
            cod_municipio="38490",
            zona=1,
            secao=42,
            data_hora=datetime(2022, 10, 2, 8, 0, 0),
            severidade="INF",
            codigo_evento="00010",
            mensagem="Votação iniciada",
        ),
        UrnaLogRecord(
            ano=2022,
            turno=1,
            uf="BA",
            cod_municipio="38490",
            zona=1,
            secao=42,
            data_hora=datetime(2022, 10, 2, 8, 2, 30),
            severidade="INF",
            codigo_evento="00020",
            mensagem="Eleitor habilitado por biometria",
        ),
    ]


def test_save_and_read_parquet(tmp_path: Path, sample_records):
    parquet_file = tmp_path / "test_logs.parquet"
    UrnaStorage.save_to_parquet(sample_records, parquet_file)

    assert parquet_file.exists()
    table = pq.read_table(parquet_file)
    assert table.num_rows == 2
    assert "codigo_evento" in table.column_names
    assert "modelo_urna" in table.column_names


def test_save_and_read_csv(tmp_path: Path, sample_records):
    csv_file = tmp_path / "test_logs.csv"
    UrnaStorage.save_to_csv(sample_records, csv_file)

    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8")
    assert "Votação iniciada" in content
    assert "38490" in content


def test_save_and_query_duckdb(tmp_path: Path, sample_records):
    db_file = tmp_path / "test_db.duckdb"
    UrnaStorage.save_to_duckdb(sample_records, db_file, table_name="test_logs")

    assert db_file.exists()
    rows = UrnaStorage.query_duckdb("SELECT COUNT(*) FROM test_logs", db_file)
    assert rows[0][0] == 2

    rows_detail = UrnaStorage.query_duckdb(
        "SELECT codigo_evento, mensagem FROM test_logs WHERE zona = 1", db_file
    )
    assert len(rows_detail) == 2
    assert rows_detail[0][0] == "00010"
