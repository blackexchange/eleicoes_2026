"""
Módulo de Métricas e Análise de Auditoria de Logs de Urna.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
from typing import Any, Dict, List, Optional
from src.parser import UrnaLogRecord


@dataclass
class VoterSession:
    inicio: datetime
    fim: datetime
    duracao_segundos: float


class UrnaMetricsAnalyzer:
    """
    Analisa eventos do logd.dat para extrair métricas de fluxo eleitoral, tempos e anomalias.
    """

    # Padrões de mensagens oficiais do TSE
    HABILITACAO_KEYWORDS = [
        "eleitor foi habilitado",
        "título digitado pelo mesário",
        "titulo digitado pelo mesario",
        "solicita digital",
        "habilitado",
        "habilitação",
        "habilita",
        "digitação do título",
        "biometria",
        "liberada para votação",
    ]
    VOTO_CONFIRMADO_KEYWORDS = [
        "o voto do eleitor foi computado",
        "voto confirmado para [presidente]",
        "voto confirmado",
        "voto registrado",
        "fim de votação do eleitor",
    ]
    ANOMALIA_KEYWORDS = [
        "erro",
        "falha",
        "reinici",
        "travamento",
        "substituição",
        "interrupção",
        "bateria",
        "desligada",
        "tecla indevida",
    ]

    @classmethod
    def compute_voting_times(cls, records: List[UrnaLogRecord]) -> Dict[str, Any]:
        """
        Calcula os tempos individuais de votação (em segundos) e agregações estatísticas.
        """
        # Ordena por timestamp
        sorted_records = sorted(records, key=lambda r: r.data_hora)
        
        sessions: List[VoterSession] = []
        current_start: Optional[datetime] = None

        for rec in sorted_records:
            msg_lower = rec.mensagem.lower()

            # Início de atendimento do eleitor
            if any(k in msg_lower for k in cls.HABILITACAO_KEYWORDS):
                if current_start is None:
                    current_start = rec.data_hora

            # Voto confirmado / finalizado
            elif any(k in msg_lower for k in cls.VOTO_CONFIRMADO_KEYWORDS):
                if current_start is not None:
                    duration = (rec.data_hora - current_start).total_seconds()
                    # Filtra tempos absurdos (> 30 min ou <= 0)
                    if 0 < duration <= 1800:
                        sessions.append(VoterSession(
                            inicio=current_start,
                            fim=rec.data_hora,
                            duracao_segundos=duration
                        ))
                    current_start = None

        durations = [s.duracao_segundos for s in sessions]
        if not durations:
            return {
                "total_eleitores_processados": 0,
                "tempo_medio_segundos": 0.0,
                "tempo_mediano_segundos": 0.0,
                "tempo_min_segundos": 0.0,
                "tempo_max_segundos": 0.0,
                "desvio_padrao": 0.0,
            }

        return {
            "total_eleitores_processados": len(durations),
            "tempo_medio_segundos": round(statistics.mean(durations), 2),
            "tempo_mediano_segundos": round(statistics.median(durations), 2),
            "tempo_min_segundos": round(min(durations), 2),
            "tempo_max_segundos": round(max(durations), 2),
            "desvio_padrao": round(statistics.stdev(durations), 2) if len(durations) > 1 else 0.0,
        }

    @classmethod
    def compute_hourly_traffic(cls, records: List[UrnaLogRecord]) -> Dict[str, int]:
        """
        Calcula o total de votos concluídos por faixa horária (ex: 08:00-08:59).
        """
        hourly_counts: Dict[str, int] = defaultdict(int)

        for rec in records:
            msg_lower = rec.mensagem.lower()
            if any(k in msg_lower for k in cls.VOTO_CONFIRMADO_KEYWORDS):
                hour_str = f"{rec.data_hora.hour:02d}:00"
                hourly_counts[hour_str] += 1

        # Preenche as horas padrão da eleição (08h às 17h)
        full_timeline = {f"{h:02d}:00": hourly_counts[f"{h:02d}:00"] for h in range(8, 18)}
        return full_timeline

    @classmethod
    def detect_anomalies_and_restarts(cls, records: List[UrnaLogRecord]) -> List[Dict[str, Any]]:
        """
        Detecta eventos de atenção, avisos de sistema, quedas e reinicializações.
        """
        anomalies: List[Dict[str, Any]] = []

        for rec in records:
            msg_lower = rec.mensagem.lower()
            if rec.severidade in ("WAR", "ERR", "ALR") or any(k in msg_lower for k in cls.ANOMALIA_KEYWORDS):
                anomalies.append({
                    "data_hora": rec.data_hora.isoformat(),
                    "severidade": rec.severidade,
                    "codigo_evento": rec.codigo_evento,
                    "mensagem": rec.mensagem,
                    "zona": rec.zona,
                    "secao": rec.secao,
                })

        return anomalies
