"""
Módulo de Download e Resolução de URLs do TSE para arquivos LOGJEZ de Urnas Eletrônicas.
"""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import httpx
from tqdm.asyncio import tqdm_asyncio


class TSEUrlBuilder:
    """
    Construtor e resolvedor de URLs para arquivos de urna do TSE.
    """

    DEFAULT_ELECTION_CODES = {
        # 2022: Eleições Gerais
        (2022, 1): "544",
        (2022, 2): "545",
        # 2024: Eleições Municipais
        (2024, 1): "619",
        (2024, 2): "620",
        # 2026: Eleições Gerais (Configurável/Previsto)
        (2026, 1): "700",
        (2026, 2): "701",
    }

    BASE_CDN_URL = "https://resultados.tse.jus.br/oficial"
    BASE_DADOS_ABERTOS_URL = "https://cdn.tse.jus.br/estatistica/sead/eleicoes"

    @classmethod
    def get_election_code(cls, ano: int, turno: int) -> str:
        return cls.DEFAULT_ELECTION_CODES.get((ano, turno), "544")

    @classmethod
    def build_package_url(cls, ano: int, turno: int, uf: str) -> str:
        """
        Retorna a URL do pacote compactado estadual de arquivos de urna (.zip contendo .logjez)
        disponibilizado no repositório oficial de Dados Abertos do TSE.
        """
        uf = uf.upper()
        return (
            f"{cls.BASE_DADOS_ABERTOS_URL}/eleicoes{ano}/arqurnatot/"
            f"bu_imgbu_logjez_rdv_vscmr_{ano}_{turno}t_{uf}.zip"
        )

    @classmethod
    def build_section_url(
        cls,
        ano: int,
        turno: int,
        uf: str,
        cod_municipio: str,
        zona: int,
        secao: int,
        hash_arquivo: Optional[str] = None,
    ) -> str:
        """
        Retorna a URL direta do CDN de arquivos de urna para uma seção eleitoral específica.
        """
        uf = uf.lower()
        cod_eleicao = cls.get_election_code(ano, turno)
        mun_str = str(cod_municipio).zfill(5)
        zona_str = str(zona).zfill(4)
        secao_str = str(secao).zfill(4)

        if hash_arquivo:
            return (
                f"{cls.BASE_CDN_URL}/ele{ano}/{cod_eleicao}/arquivo-urna/{hash_arquivo}/"
                f"{uf}/{mun_str}/{zona_str}/{secao_str}/o00{cod_eleicao}-{mun_str}{zona_str}{secao_str}.logjez"
            )
        else:
            return (
                f"{cls.BASE_CDN_URL}/ele{ano}/{cod_eleicao}/dados-simplificados/"
                f"{uf}/{uf}-p000{cod_eleicao}-cs.json"
            )


class UrnaDownloader:
    """
    Downloader assíncrono com suporte a concorrência, retries, backoff e cache.
    """

    def __init__(
        self,
        cache_dir: Union[str, Path] = "data/logs",
        max_concurrency: int = 10,
        timeout: float = 30.0,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.timeout = timeout

    @staticmethod
    def calculate_file_hash(filepath: Union[str, Path]) -> str:
        """Calcula o hash SHA-256 de um arquivo local."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def is_cached_and_valid(self, destination: Path, expected_min_size: int = 100) -> bool:
        """Verifica se o arquivo já existe localmente e possui tamanho válido."""
        return destination.exists() and destination.stat().st_size >= expected_min_size

    async def download_file(
        self,
        client: httpx.AsyncClient,
        url: str,
        destination: Path,
        retries: int = 3,
        backoff_factor: float = 1.5,
    ) -> Tuple[bool, str]:
        """
        Baixa um arquivo com retries exponenciais e controle de taxa.
        """
        if self.is_cached_and_valid(destination):
            return True, f"CACHE_HIT: {destination}"

        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_dest = destination.with_suffix(destination.suffix + ".tmp")

        async with self.semaphore:
            for attempt in range(1, retries + 1):
                try:
                    response = await client.get(url, follow_redirects=True, timeout=self.timeout)
                    if response.status_code == 200:
                        temp_dest.write_bytes(response.content)
                        temp_dest.replace(destination)
                        return True, f"DOWNLOAD_OK: {destination}"
                    elif response.status_code == 404:
                        return False, f"HTTP_404_NOT_FOUND: {url}"
                    elif response.status_code == 429:
                        # Rate limit: aguarda com backoff maior
                        wait_time = backoff_factor ** attempt * 2
                        await asyncio.sleep(wait_time)
                    else:
                        await asyncio.sleep(backoff_factor ** attempt)
                except (httpx.RequestError, httpx.TimeoutException) as exc:
                    if attempt == retries:
                        return False, f"ERROR_FAILED: {str(exc)}"
                    await asyncio.sleep(backoff_factor ** attempt)

        return False, f"ERROR_MAX_RETRIES: {url}"

    async def download_batch(
        self,
        items: List[Dict[str, Union[str, Path]]],
        show_progress: bool = True,
    ) -> List[Tuple[bool, str]]:
        """
        Executa o download de múltiplos itens em paralelo.
        Cada item deve ser um dict contendo {'url': str, 'destination': Path/str}.
        """
        async with httpx.AsyncClient(headers={"User-Agent": "TSE-Log-Urna-Pipeline/1.0"}) as client:
            tasks = [
                self.download_file(
                    client=client,
                    url=str(item["url"]),
                    destination=Path(item["destination"]),
                )
                for item in items
            ]
            if show_progress:
                return await tqdm_asyncio.gather(*tasks, desc="Baixando arquivos de urna")
            return await asyncio.gather(*tasks)
