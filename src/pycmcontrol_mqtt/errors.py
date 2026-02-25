# src/pycmcontrol_mqtt/errors.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


# -------------------------
# Base
# -------------------------
class CmcError(Exception):
    """Erro base da biblioteca."""
    pass


# -------------------------
# Config / Usage
# -------------------------
class CmcConfigError(CmcError):
    """Configuração inválida (ex: faltou api_user/api_pass)."""
    pass


class CmcNotConnected(CmcError):
    """Operação requer conexão MQTT, mas connect() não foi chamado."""
    pass


class CmcInvalidArgument(CmcError):
    """Argumento inválido fornecido pelo usuário da biblioteca."""
    pass


# -------------------------
# Network / MQTT transport
# -------------------------
class CmcConnectionError(CmcError):
    """Falha ao conectar no broker (DNS, timeout, firewall, rota, etc)."""
    pass


class CmcConnectionTimeout(CmcConnectionError):
    """Timeout durante connect TCP/MQTT."""
    pass


class CmcDnsError(CmcConnectionError):
    """Hostname não resolve (DNS)."""
    pass


class CmcTlsError(CmcConnectionError):
    """Erro de TLS/SSL (certificado, handshake, etc)."""
    pass


class CmcMqttProtocolError(CmcConnectionError):
    """Erro de protocolo MQTT (versão, pacote inválido, etc)."""
    pass


class CmcMqttAuthError(CmcConnectionError):
    """Broker rejeitou usuário/senha (CONNACK rc != 0)."""
    def __init__(self, rc: int, message: str = ""):
        super().__init__(message or f"Falha de autenticação MQTT (rc={rc})")
        self.rc = rc


class CmcDisconnected(CmcError):
    """Conexão caiu durante uma operação."""
    pass


# -------------------------
# Requests / Responses
# -------------------------
class CmcTimeout(CmcError):
    """Timeout esperando resposta no tópico /get."""
    pass


@dataclass
class CmcResponseError(CmcError):
    """
    Erro retornado pelo CmControl em uma resposta JSON.
    Ex.: status != 200, ou 200 com log indicando erro de negócio.
    """
    status: Optional[str] = None
    log: str = ""
    endpoint: str = ""
    raw: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        base = f"CmControl respondeu erro"
        if self.endpoint:
            base += f" em '{self.endpoint}'"
        if self.status:
            base += f" (status={self.status})"
        if self.log:
            base += f": {self.log}"
        return base


class CmcLoginError(CmcResponseError):
    """Erro específico de login OAuth2."""
    pass


class CmcApiError(CmcResponseError):
    """Erro genérico de chamadas REST via MQTT+REST."""
    pass


class CmcApontamentoError(CmcResponseError):
    """Erro de apontamento (setup.apontamento)."""
    pass


# -------------------------
# Internal / Parse
# -------------------------
class CmcDecodeError(CmcError):
    """Payload recebido não é JSON válido ou está corrompido."""
    pass