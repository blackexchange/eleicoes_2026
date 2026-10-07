"""
Módulo de Armazenamento e Exportação Analítica (Parquet, DuckDB, CSV).
"""

import os
from pathlib import Path
from typing import Any, List, Optional, Union
import duckdb
import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq
from src.parser import UrnaLogRecord


class UrnaStorage:
    """
    Gerenciador de persistência para eventos de logs de urnas em formatos analíticos.
    """

    ARROW_SCHEMA = pa.schema([
        ("ano", pa.int32()),
        ("turno", pa.int32()),
        ("uf", pa.string()),
        ("cod_municipio", pa.string()),
        ("zona", pa.int32()),
        ("secao", pa.int32()),
        ("data_hora", pa.timestamp("us")),
        ("severidade", pa.string()),
        ("codigo_evento", pa.string()),
        ("mensagem", pa.string()),
        ("modelo_urna", pa.string()),
    ])

    @classmethod
    def records_to_pyarrow_table(cls, records: List[UrnaLogRecord]) -> pa.Table:
        """Converte uma lista de UrnaLogRecord em uma PyArrow Table estruturada."""
        if not records:
            return pa.Table.from_batches([], schema=cls.ARROW_SCHEMA)

        data_dict = {
            "ano": [r.ano for r in records],
            "turno": [r.turno for r in records],
            "uf": [r.uf for r in records],
            "cod_municipio": [r.cod_municipio for r in records],
            "zona": [r.zona for r in records],
            "secao": [r.secao for r in records],
            "data_hora": [r.data_hora for r in records],
            "severidade": [r.severidade for r in records],
            "codigo_evento": [r.codigo_evento for r in records],
            "mensagem": [r.mensagem for r in records],
            "modelo_urna": [r.modelo_urna for r in records],
        }
        return pa.Table.from_pydict(data_dict, schema=cls.ARROW_SCHEMA)

    @classmethod
    def save_to_parquet(
        cls,
        records: List[UrnaLogRecord],
        output_path: Union[str, Path],
        partition_cols: Optional[List[str]] = None,
        compression: str = "snappy",
    ) -> Path:
        """
        Salva os registros em arquivo ou diretório particionado Parquet.
        """
        path = Path(output_path)
        table = cls.records_to_pyarrow_table(records)

        if partition_cols:
            path.mkdir(parents=True, exist_ok=True)
            pq.write_to_dataset(
                table,
                root_path=str(path),
                partition_cols=partition_cols,
                compression=compression,
            )
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(table, str(path), compression=compression)

        return path

    @classmethod
    def save_to_csv(cls, records: List[UrnaLogRecord], output_path: Union[str, Path]) -> Path:
        """
        Exporta os registros para arquivo CSV formatado.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        table = cls.records_to_pyarrow_table(records)
        pcsv.write_csv(table, str(path))
        return path

    @classmethod
    def save_to_duckdb(
        cls,
        records: List[UrnaLogRecord],
        db_path: Union[str, Path] = "data/processed/eleicoes.duckdb",
        table_name: str = "logs_urnas",
    ) -> Path:
        """
        Persiste os registros em uma tabela DuckDB.
        """
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        table = cls.records_to_pyarrow_table(records)

        con = duckdb.connect(str(db_path))
        try:
            # Registra tabela / insere dados
            con.register("temp_arrow_table", table)
            con.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} AS 
                SELECT * FROM temp_arrow_table WHERE 1=0
            """)
            con.execute(f"INSERT INTO {table_name} SELECT * FROM temp_arrow_table")
        finally:
            con.close()

        return db_path

    @classmethod
    def query_duckdb(cls, query: str, db_path: Union[str, Path]) -> List[Any]:
        """
        Executa uma consulta SQL em um arquivo DuckDB e retorna os resultados.
        """
        con = duckdb.connect(str(db_path), read_only=True)
        try:
            return con.execute(query).fetchall()
        finally:
            con.close()
