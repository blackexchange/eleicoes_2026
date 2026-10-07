"""
CLI e Orquestrador Principal do Pipeline de Logs das Urnas do TSE.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

# Garante suporte a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Garante inclusão do root do projeto no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.downloader import TSEUrlBuilder, UrnaDownloader
from src.metrics import UrnaMetricsAnalyzer
from src.parser import LogJezParser, UrnaLogRecord
from src.storage import UrnaStorage


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline de Extração, Parsing e Análise de Logs das Urnas (LOGJEZ) do TSE.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--ano", type=int, default=2022, help="Ano da eleição (ex: 2022, 2024, 2026)")
    parser.add_argument("--turno", type=int, default=1, choices=[1, 2], help="Turno da eleição")
    parser.add_argument("--uf", type=str, default="BA", help="Sigla da Unidade Federativa (ex: BA, SP, RJ)")
    parser.add_argument("--municipio", type=str, default="38490", help="Código do Município TSE (ex: 38490 Salvador)")
    parser.add_argument("--zona", type=int, default=1, help="Número da Zona Eleitoral")
    parser.add_argument("--secao", type=int, default=1, help="Número da Seção Eleitoral")
    parser.add_argument("--file", type=str, default=None, help="Caminho para arquivo .logjez ou logd.dat local existente")
    parser.add_argument("--max-sections", type=int, default=None, help="Número máximo de seções a processar (None = todas)")
    parser.add_argument(
        "--format",
        type=str,
        default="parquet",
        choices=["parquet", "duckdb", "csv", "all"],
        help="Formato de saída dos dados processados",
    )
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Diretório de saída")
    parser.add_argument("--no-metrics", action="store_true", help="Não exibir métricas no terminal")
    return parser.parse_args()


async def run_pipeline(args: argparse.Namespace) -> List[UrnaLogRecord]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_cache_dir = Path("data/logs")
    logs_cache_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "ano": args.ano,
        "turno": args.turno,
        "uf": args.uf.upper(),
        "cod_municipio": args.municipio,
        "zona": args.zona,
        "secao": args.secao,
    }

    records: List[UrnaLogRecord] = []

    # Caso 1: Processamento de arquivo local
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Erro: Arquivo local '{file_path}' não encontrado.", file=sys.stderr)
            return []
        print(f"📂 Processando arquivo local: {file_path}")
        if file_path.name.lower().endswith(".zip"):
            records = LogJezParser.parse_tse_package_zip(file_path, metadata, max_sections=args.max_sections)
        else:
            records = LogJezParser.parse_file(file_path, metadata)

    # Caso 2: Download do pacote oficial do TSE
    else:
        print(f"🌐 Iniciando pipeline para UF: {args.uf.upper()} | Ano: {args.ano} | Turno: {args.turno}")
        downloader = UrnaDownloader(cache_dir=logs_cache_dir)

        # Nome padronizado do pacote estadual
        target_file = logs_cache_dir / f"bu_imgbu_logjez_rdv_vscmr_{args.ano}_{args.turno}t_{args.uf.upper()}.zip"

        if downloader.is_cached_and_valid(target_file, expected_min_size=1024 * 1024):
            print(f"⚡ Cache Hit: Pacote local encontrado em {target_file}")
        else:
            url = TSEUrlBuilder.build_package_url(args.ano, args.turno, args.uf)
            print(f"⬇️ Baixando pacote oficial de logs: {url}")
            items = [{"url": url, "destination": target_file}]
            results = await downloader.download_batch(items, show_progress=True)
            success, msg = results[0]
            if not success:
                print(f"❌ Erro ao baixar arquivo remoto: {msg}")
                return []

        if target_file.exists():
            print(f"📦 Descompactando e processando seções (.logjez) do pacote {args.uf.upper()}...")
            records = LogJezParser.parse_tse_package_zip(
                target_file, default_metadata=metadata, max_sections=args.max_sections
            )

    if not records:
        print("ℹ️ Nenhum registro de log foi processado.")
        return []

    print(f"✅ Total de eventos decodificados: {len(records):,}")

    # Salva nos formatos solicitados
    if args.format in ("parquet", "all"):
        pq_path = output_dir / f"logs_{args.ano}_T{args.turno}_{args.uf.upper()}.parquet"
        UrnaStorage.save_to_parquet(records, pq_path)
        print(f"📦 Arquivo Parquet salvo em: {pq_path}")

    if args.format in ("csv", "all"):
        csv_path = output_dir / f"logs_{args.ano}_T{args.turno}_{args.uf.upper()}.csv"
        UrnaStorage.save_to_csv(records, csv_path)
        print(f"📄 Arquivo CSV salvo em: {csv_path}")

    if args.format in ("duckdb", "all"):
        db_path = output_dir / "eleicoes.duckdb"
        UrnaStorage.save_to_duckdb(records, db_path)
        print(f"🦆 Dados persistidos no DuckDB em: {db_path}")

    # Exibe métricas de auditoria
    if not args.no_metrics:
        times = UrnaMetricsAnalyzer.compute_voting_times(records)
        hourly = UrnaMetricsAnalyzer.compute_hourly_traffic(records)
        anomalies = UrnaMetricsAnalyzer.detect_anomalies_and_restarts(records)

        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE AUDITORIA & MÉTRICAS DA URNA")
        print("=" * 60)
        print(f"• Eleitores que votaram: {times['total_eleitores_processados']}")
        print(f"• Tempo médio na cabine: {times['tempo_medio_segundos']}s")
        print(f"• Tempo mediano: {times['tempo_mediano_segundos']}s (Min: {times['tempo_min_segundos']}s | Max: {times['tempo_max_segundos']}s)")
        print(f"• Desvio padrão do tempo: {times['desvio_padrao']}s")
        print("\n📈 Fluxo de Votos por Faixa Horária:")
        max_hourly = max(hourly.values()) if hourly.values() and max(hourly.values()) > 0 else 1
        for hour, count in hourly.items():
            bar_len = int((count / max_hourly) * 35)
            bar = "█" * bar_len if count > 0 else ""
            print(f"  [{hour}] {count:5d} votos  | {bar}")

        print(f"\n⚠️ Intercorrências / Avisos de Sistema: {len(anomalies)}")
        for a in anomalies[:5]:
            print(f"  - [{a['data_hora']}] [{a['severidade']}] {a['mensagem']}")
        if len(anomalies) > 5:
            print(f"  ... e mais {len(anomalies) - 5} eventos.")
        print("=" * 60 + "\n")

    return records


def main():
    args = parse_arguments()
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
