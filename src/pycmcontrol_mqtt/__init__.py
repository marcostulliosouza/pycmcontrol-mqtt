"""
pycmcontrol-mqtt

Cliente MQTT para Driver CmControl v1.00 (MQTT + MQTT+REST + OAuth2)
"""

from .config import CmControlConfig
from .client import CmControlClient, BrokerTLS

from .models import (
    SetupApontamento,
    Apontamento,
    Serial,
    OrdemTransporte,
    Evidence,
)

from .errors import (
    CmcError,
    CmcConfigError,
    CmcNotConnected,
    CmcInvalidArgument,
    CmcConnectionError,
    CmcConnectionTimeout,
    CmcDnsError,
    CmcTlsError,
    CmcMqttProtocolError,
    CmcMqttAuthError,
    CmcDisconnected,
    CmcTimeout,
    CmcDecodeError,
    CmcLoginError,
    CmcApiError,
    CmcApontamentoError,
    CmcResponseError,
)

__all__ = [
    "CmControlClient",
    "BrokerTLS",
    "CmControlConfig",
    "SetupApontamento",
    "Apontamento",
    "Serial",
    "OrdemTransporte",
    "Evidence",
    "CmcError",
    "CmcConfigError",
    "CmcNotConnected",
    "CmcInvalidArgument",
    "CmcConnectionError",
    "CmcConnectionTimeout",
    "CmcDnsError",
    "CmcTlsError",
    "CmcMqttProtocolError",
    "CmcMqttAuthError",
    "CmcDisconnected",
    "CmcTimeout",
    "CmcDecodeError",
    "CmcLoginError",
    "CmcApiError",
    "CmcApontamentoError",
    "CmcResponseError",
]

