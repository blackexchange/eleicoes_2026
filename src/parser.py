"""
Módulo de Descompactação e Parsing de arquivos LOGJEZ (logd.dat) das Urnas Eletrônicas do TSE.
"""

import io
import os
import re
import tarfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union


@dataclass
class UrnaLogRecord:
    ano: int
    turno: int
    uf: str
    cod_municipio: str
    zona: int
    secao: int
    data_hora: datetime
    severidade: str
    codigo_evento: str
    mensagem: str
    modelo_urna: str = "DESCONHECIDO"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["data_hora"] = self.data_hora.isoformat()
        return d


class LogJezParser:
    """
    Parser especializado em containers .logjez e decodificação do logd.dat.
    """

    # Expressão regular para linhas do logd.dat:
    # Exemplo: 02/10/2022 08:00:15\tINF\t00010\tMensagem do evento
    # Ou separado por múltiplos espaços
    LOG_LINE_REGEX = re.compile(
        r"^(?P<data>\d{2}/\d{2}/\d{4})\s+(?P<hora>\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+"
        r"(?P<severidade>[A-Z]{3,4})\s+(?P<codigo>\d+|[A-Z0-9_-]+)\s+(?P<mensagem>.*)$"
    )

    @classmethod
    def detect_urna_model(cls, raw_text: str) -> str:
        """
        Detecta o modelo da urna eletrônica (ex: UE2020, UE2015, UE2013, UE2011, UE2009, UE2022)
        a partir das assinaturas de hardware registradas no logd.dat.
        """
        # Padrão 1: Biblioteca de hardware (/uenux/lib/avusrlibue2020.vst)
        match = re.search(r"avusrlib(ue20\d{2})", raw_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Padrão 2: Modelo explícito em texto
        match = re.search(r"(?:modelo|hardware|urna)\s*[:=-]?\s*(ue20\d{2})", raw_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Padrão 3: Qualquer menção a UE20xx
        match = re.search(r"\b(UE20\d{2})\b", raw_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        return "OUTRO"

    @classmethod
    def extract_logd_content(cls, file_input: Union[str, Path, bytes, io.BytesIO]) -> str:
        """
        Extrai o conteúdo do arquivo 'logd.dat' de dentro de um container .logjez (7z, zip ou tar).
        """
        if isinstance(file_input, (str, Path)):
            with open(file_input, "rb") as f:
                data = f.read()
        elif isinstance(file_input, io.BytesIO):
            data = file_input.getvalue()
        else:
            data = file_input

        # Tentativa 1: Container 7-Zip (formato padrão do TSE .logjez)
        try:
            import py7zr
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                with py7zr.SevenZipFile(io.BytesIO(data), "r") as szf:
                    szf.extractall(path=tmpdir)
                for root, _, files in os.walk(tmpdir):
                    for fn in files:
                        if fn.endswith("logd.dat") or "logd" in fn.lower():
                            with open(os.path.join(root, fn), "rb") as lf:
                                return cls._decode_bytes(lf.read())
        except Exception:
            pass

        # Tentativa 2: Container ZIP
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for filename in zf.namelist():
                    if filename.endswith("logd.dat") or "logd" in filename.lower():
                        raw_bytes = zf.read(filename)
                        return cls._decode_bytes(raw_bytes)
        except (zipfile.BadZipFile, Exception):
            pass

        # Tentativa 3: Container TAR / GZ
        try:
            with tarfile.open(fileobj=io.BytesIO(data)) as tf:
                for member in tf.getmembers():
                    if member.name.endswith("logd.dat") or "logd" in member.name.lower():
                        f = tf.extractfile(member)
                        if f is not None:
                            raw_bytes = f.read()
                            return cls._decode_bytes(raw_bytes)
        except Exception:
            pass

        # Tentativa 4: Conteúdo de texto direto (já descompactado)
        return cls._decode_bytes(data)

    @staticmethod
    def _decode_bytes(raw_bytes: bytes) -> str:
        """Tenta decodificar bytes em UTF-8, Latin-1 ou CP1252 com fallback."""
        for encoding in ("utf-8", "latin-1", "cp1252", "iso-8859-1"):
            try:
                return raw_bytes.decode(encoding)
            except (UnicodeDecodeError, AttributeError):
                continue
        return raw_bytes.decode("utf-8", errors="replace")

    @classmethod
    def parse_line(
        cls, line: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UrnaLogRecord]:
        """
        Decodifica uma linha do logd.dat em um UrnaLogRecord estruturado.
        """
        line = line.strip()
        if not line:
            return None

        # Suporte ao formato oficial TSE delimitado por TABs:
        # Ex: DataHora \t Severidade \t CodUrna \t Modulo \t Mensagem \t HMAC
        parts = line.split("\t")
        if len(parts) >= 5:
            dt_str = parts[0].strip()
            sev = parts[1].strip()
            cod = f"{parts[2].strip()}:{parts[3].strip()}"
            msg = parts[4].strip()
            try:
                dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                dt = datetime.now()
        elif len(parts) == 4:
            dt_str = parts[0].strip()
            sev = parts[1].strip()
            cod = parts[2].strip()
            msg = parts[3].strip()
            try:
                dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                dt = datetime.now()
        else:
            match = cls.LOG_LINE_REGEX.match(line)
            if not match:
                return None
            d = match.groupdict()
            dt_str = f"{d['data']} {d['hora']}"
            if "." in d["hora"]:
                dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S.%f")
            else:
                dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
            sev = d["severidade"]
            cod = d["codigo"]
            msg = d["mensagem"]

        meta = metadata or {}
        return UrnaLogRecord(
            ano=int(meta.get("ano", 2026)),
            turno=int(meta.get("turno", 1)),
            uf=str(meta.get("uf", "BA")).upper(),
            cod_municipio=str(meta.get("cod_municipio", "00000")),
            zona=int(meta.get("zona", 0)),
            secao=int(meta.get("secao", 0)),
            data_hora=dt,
            severidade=sev,
            codigo_evento=cod,
            mensagem=msg,
            modelo_urna=str(meta.get("modelo_urna", "DESCONHECIDO")).upper(),
        )

    @classmethod
    def parse_text(
        cls, raw_text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[UrnaLogRecord]:
        """
        Processa todo o texto de um logd.dat e retorna lista de registros.
        """
        meta = dict(metadata or {})
        if "modelo_urna" not in meta or meta["modelo_urna"] == "DESCONHECIDO":
            meta["modelo_urna"] = cls.detect_urna_model(raw_text)

        records: List[UrnaLogRecord] = []
        for line in raw_text.splitlines():
            rec = cls.parse_line(line, meta)
            if rec:
                records.append(rec)
        return records

    @classmethod
    def parse_file(
        cls, file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None
    ) -> List[UrnaLogRecord]:
        """
        Lê um arquivo .logjez ou .dat e retorna todos os registros de log estruturados.
        """
        raw_text = cls.extract_logd_content(file_path)
        return cls.parse_text(raw_text, metadata)

    @classmethod
    def parse_tse_package_zip(
        cls,
        zip_path: Union[str, Path],
        default_metadata: Optional[Dict[str, Any]] = None,
        max_sections: Optional[int] = None,
    ) -> List[UrnaLogRecord]:
        """
        Abre o pacote estadual ZIP do TSE, encontra todos os arquivos .logjez internos
        e processa os registros de cada seção eleitoral.
        """
        zip_path = Path(zip_path)
        all_records: List[UrnaLogRecord] = []
        base_meta = default_metadata or {}

        filename_pattern = re.compile(
            r".*-(?P<mun>\d{5})(?P<zona>\d{4})(?P<secao>\d{4})\.logjez$",
            re.IGNORECASE,
        )

        with zipfile.ZipFile(zip_path, "r") as archive:
            logjez_names = [n for n in archive.namelist() if n.lower().endswith(".logjez")]
            if max_sections:
                logjez_names = logjez_names[:max_sections]

            for name in logjez_names:
                match = filename_pattern.search(name)
                section_meta = dict(base_meta)
                if match:
                    section_meta["cod_municipio"] = match.group("mun")
                    section_meta["zona"] = int(match.group("zona"))
                    section_meta["secao"] = int(match.group("secao"))

                logjez_bytes = archive.read(name)
                logd_text = cls.extract_logd_content(logjez_bytes)
                records = cls.parse_text(logd_text, section_meta)
                all_records.extend(records)

        return all_records

