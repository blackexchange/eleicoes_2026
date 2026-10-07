"""
Testes unitários para o módulo parser.py
"""

import io
import zipfile
from datetime import datetime
from pathlib import Path
import pytest
from src.parser import LogJezParser, UrnaLogRecord


SAMPLE_LOG_TEXT = """02/10/2022 07:00:00\tINF\t00001\tUrna ligada em modo oficial
02/10/2022 07:05:00\tINF\t00002\tEmissao da Zeresima iniciada
02/10/2022 08:00:00\tINF\t00010\tVotacao iniciada
02/10/2022 08:02:15\tINF\t00020\tEleitor habilitado por biometria
02/10/2022 08:03:00\tINF\t00021\tVoto confirmado para todos os cargos
02/10/2022 17:00:00\tINF\t00030\tEncerramento da votacao
02/10/2022 17:00:15\tINF\t00035\tEmissao do Boletim de Urna (BU)
"""


def test_parse_individual_line():
    line = "02/10/2022 08:02:15\tINF\t00020\tEleitor habilitado por biometria"
    meta = {
        "ano": 2022,
        "turno": 1,
        "uf": "BA",
        "cod_municipio": "38490",
        "zona": 1,
        "secao": 42,
    }
    rec = LogJezParser.parse_line(line, meta)
    assert rec is not None
    assert rec.ano == 2022
    assert rec.turno == 1
    assert rec.uf == "BA"
    assert rec.cod_municipio == "38490"
    assert rec.zona == 1
    assert rec.secao == 42
    assert rec.data_hora == datetime(2022, 10, 2, 8, 2, 15)
    assert rec.severidade == "INF"
    assert rec.codigo_evento == "00020"
    assert "Eleitor habilitado" in rec.mensagem


def test_parse_text_multiple_lines():
    meta = {"ano": 2022, "turno": 1, "uf": "BA", "zona": 1, "secao": 10}
    records = LogJezParser.parse_text(SAMPLE_LOG_TEXT, meta)
    assert len(records) == 7
    assert records[0].codigo_evento == "00001"
    assert records[-1].codigo_evento == "00035"


def test_extract_and_parse_from_zip():
    # Cria container .logjez (zip em memória)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("logd.dat", SAMPLE_LOG_TEXT.encode("utf-8"))
        zf.writestr("assinatura.vsec", b"DUMMY_SIGNATURE_BYTES")

    buf.seek(0)
    content = LogJezParser.extract_logd_content(buf)
    assert "Urna ligada em modo oficial" in content
    assert "Emissao do Boletim de Urna" in content

    records = LogJezParser.parse_text(content, {"ano": 2022, "uf": "BA"})
    assert len(records) == 7


def test_detect_urna_model():
    log_ue2020 = "INFO\tSCUE\tVerificação de assinatura [/uenux/lib/avusrlibue2020.vst]\tOK"
    assert LogJezParser.detect_urna_model(log_ue2020) == "UE2020"

    log_ue2015 = "INFO\tSCUE\tVerificação de assinatura [/uenux/lib/avusrlibue2015.vst]\tOK"
    assert LogJezParser.detect_urna_model(log_ue2015) == "UE2015"

    log_ue2013 = "INFO\tSCUE\tHardware UE2013 inicializado com sucesso"
    assert LogJezParser.detect_urna_model(log_ue2013) == "UE2013"
