"""
Testes unitários para o módulo downloader.py
"""

import pytest
from pathlib import Path
from src.downloader import TSEUrlBuilder, UrnaDownloader


def test_tse_url_builder_package_url():
    url = TSEUrlBuilder.build_package_url(ano=2022, turno=1, uf="BA")
    assert "eleicoes2022" in url
    assert "bu_imgbu_logjez_rdv_vscmr_2022_1t_BA.zip" in url


def test_tse_url_builder_section_url():
    url = TSEUrlBuilder.build_section_url(
        ano=2022,
        turno=1,
        uf="BA",
        cod_municipio="38490",
        zona=1,
        secao=42,
        hash_arquivo="abc123hash",
    )
    assert "arquivo-urna/abc123hash/ba/38490/0001/0042" in url
    assert ".logjez" in url


def test_urna_downloader_cache_validation(tmp_path: Path):
    downloader = UrnaDownloader(cache_dir=tmp_path)
    test_file = tmp_path / "test_file.logjez"

    # Arquivo não existe
    assert not downloader.is_cached_and_valid(test_file)

    # Arquivo vazio
    test_file.write_bytes(b"")
    assert not downloader.is_cached_and_valid(test_file, expected_min_size=10)

    # Arquivo válido com dados
    test_file.write_bytes(b"TEST_VALID_CONTENT_FOR_HASH_AND_SIZE_VALIDATION")
    assert downloader.is_cached_and_valid(test_file, expected_min_size=10)

    # Teste de hash
    file_hash = downloader.calculate_file_hash(test_file)
    assert len(file_hash) == 64
