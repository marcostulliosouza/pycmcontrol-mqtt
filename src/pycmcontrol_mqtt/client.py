from __future__ import annotations

import json
import socket
import ssl
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

import paho.mqtt.client as mqtt

from .config import CmControlConfig
from .utils import now_ts, b64
from .models import SetupApontamento, Apontamento, Serial, Evidence

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


@dataclass(frozen=True)
class BrokerTLS:
    """
    Config opcional de TLS para MQTT.
    Se seu broker usa 8883/TLS, configure aqui.

    - ca_certs: caminho do CA (opcional)
    - certfile/keyfile: client cert (opcional)
    - insecure: True = não valida hostname/cert (evite em produção)
    """
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    insecure: bool = False


class CmControlClient:
    """
    Cliente MQTT para CmControl Driver v1.00 e MQTT+REST, conforme doc.

    Regras da doc:
    - REQUEST:  br/com/cmcontrol/dispositivo/{device}/set/{endpoint}
    - RESPONSE: br/com/cmcontrol/dispositivo/{device}/get/{endpoint}
    - QoS = 0
    - Retained = false
    - Dispositivo deve ficar inscrito em: .../get/+
    - Se o sistema enviar /get/ping -> responder /set/pong {timestamp}
    - Se o sistema enviar /get/state -> responder /set/state {state:"1"}

    Recursos:
    - request(): publica /set/{endpoint} e aguarda /get/{endpoint} com cache por tópico
    - login OAuth2 via MQTT+REST
    - setup.apontamento via MQTT+REST
    - erros claros (rede, mqtt auth, status != 200, timeout de resposta, etc)
    """

    def __init__(
        self,
        cfg: CmControlConfig,
        *,
        tls: Optional[BrokerTLS] = None,
        connect_keepalive_s: int = 60,
        request_timeout_s_default: float = 10.0,
        strict_business_errors: bool = True,
        business_error_prefixes: tuple[str, ...] = ("ERRO",),
        business_error_contains: tuple[str, ...] = ("FALHA", "NOK"),
        business_ok_prefixes: tuple[str, ...] = ("ERRO4",),  # ex: "já apontado" tratar como ok
    ):
        self.cfg = cfg
        self.tls = tls
        self.connect_keepalive_s = int(connect_keepalive_s)
        self.request_timeout_s_default = float(request_timeout_s_default)

        # Regras de negócio (log/status)
        self.strict_business_errors = bool(strict_business_errors)
        self.business_error_prefixes = tuple(x.upper() for x in business_error_prefixes)
        self.business_error_contains = tuple(x.upper() for x in business_error_contains)
        self.business_ok_prefixes = tuple(x.upper() for x in business_ok_prefixes)

        self._client: Optional[mqtt.Client] = None

        # sinaliza on_connect “ok”
        self._connected = threading.Event()

        # sinaliza desconexão (queda)
        self._disconnected = threading.Event()
        self._disconnect_rc: Optional[int] = None

        # Cache de respostas por tópico (/get/...)
        self._rx_lock = threading.Lock()
        self._rx_cv = threading.Condition(self._rx_lock)
        self._rx_cache: Dict[str, Dict[str, Any]] = {}

        # Serializa requests para evitar corrida em endpoints iguais
        self._req_lock = threading.Lock()

        # Token OAuth2
        self._tok_lock = threading.Lock()
        self._access_token: Optional[str] = None
        self._token_expiration_ts: Optional[int] = None

        # Se on_connect detecta rc != 0, guardamos aqui para levantar no connect()
        self._connect_error: Optional[CmcError] = None

    # -----------------------------
    # Topics
    # -----------------------------
    def base_topic(self) -> str:
        return f"br/com/cmcontrol/dispositivo/{self.cfg.device_addr}"

    def topic_set(self, endpoint: str) -> str:
        return f"{self.base_topic()}/set/{endpoint}"

    def topic_get(self, endpoint: str) -> str:
        return f"{self.base_topic()}/get/{endpoint}"

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _ensure_client(self) -> mqtt.Client:
        if not self._client:
            raise CmcNotConnected("MQTT client não conectado. Chame connect().")
        return self._client

    @staticmethod
    def _safe_json_loads(raw: bytes) -> Dict[str, Any]:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise CmcDecodeError(f"Falha ao decodificar JSON recebido: {e}") from e

    def _raise_if_disconnected(self) -> None:
        if self._disconnected.is_set():
            raise CmcDisconnected(f"Conexão MQTT caiu (rc={self._disconnect_rc}).")

    def _api_basic_auth_header(self) -> str:
        if not (self.cfg.api_user and self.cfg.api_pass):
            raise CmcConfigError("api_user/api_pass não definidos no config (necessário para OAuth2 login).")
        return f"Basic {b64(f'{self.cfg.api_user}:{self.cfg.api_pass}')}"

    def _is_business_error(self, status: Optional[str], log: str) -> bool:
        """
        Alguns ambientes retornam status=200 com log indicando erro de negócio (ex: 'ERRO1: ...').
        Se strict_business_errors=True, tratamos isso como erro.
        """
        if not self.strict_business_errors:
            return False

        # só faz sentido quando “parece sucesso”
        if status is not None and str(status).strip() not in ("200", "200 OK"):
            return False

        up = (log or "").strip().upper()
        if not up:
            return False

        # exceções que você quer tratar como sucesso (ex: ERRO4 = já apontado)
        for okp in self.business_ok_prefixes:
            if up.startswith(okp):
                return False

        for p in self.business_error_prefixes:
            if up.startswith(p):
                return True

        for c in self.business_error_contains:
            if c in up:
                return True

        return False

    def _ensure_status_ok(
        self,
        *,
        endpoint: str,
        resp: Dict[str, Any],
        err_cls: Type[CmcResponseError],
    ) -> None:
        """
        Valida resposta padrão REST:
        {
          "status": "200",
          "log": "OK",
          "data": ...
        }
        """
        status_raw = resp.get("status")
        status = str(status_raw).strip() if status_raw is not None else None
        log = str(resp.get("log") or resp.get("message") or "").strip()

        # status != 200 => erro
        if status is not None and not status.startswith("200"):
            raise err_cls(status=status, log=log, endpoint=endpoint, raw=resp)

        # status 200 mas log indica erro de negócio => erro (se habilitado)
        if self._is_business_error(status, log):
            raise err_cls(status=status or "200", log=log, endpoint=endpoint, raw=resp)

    # -----------------------------
    # MQTT publish / request
    # -----------------------------
    def publish_set(self, endpoint: str, payload: Any) -> None:
        """
        Publica REQUEST em /set/{endpoint} com QoS=0 e retained=False (doc).
        """
        self._raise_if_disconnected()
        c = self._ensure_client()
        c.publish(self.topic_set(endpoint), json.dumps(payload), qos=0, retain=False)

    def request(self, endpoint: str, payload: Any, timeout_s: Optional[float] = None) -> Dict[str, Any]:
        """
        REQUEST: /set/{endpoint}
        RESPONSE: /get/{endpoint}

        Usa cache por tópico e aguarda até timeout.
        """
        self._raise_if_disconnected()

        timeout = self.request_timeout_s_default if timeout_s is None else float(timeout_s)
        resp_topic = self.topic_get(endpoint)

        with self._req_lock:
            # limpa cache anterior deste endpoint
            with self._rx_cv:
                self._rx_cache.pop(resp_topic, None)

            self.publish_set(endpoint, payload)

            end = time.time() + timeout
            with self._rx_cv:
                while True:
                    self._raise_if_disconnected()

                    if resp_topic in self._rx_cache:
                        return self._rx_cache[resp_topic]

                    remaining = end - time.time()
                    if remaining <= 0:
                        raise CmcTimeout(f"Timeout aguardando resposta em {resp_topic}")
                    self._rx_cv.wait(timeout=remaining)

    # -----------------------------
    # MQTT callbacks
    # -----------------------------
    def _on_connect(self, client, userdata, flags, rc):
        # rc=0 OK
        if rc != 0:
            # Não levanta exception aqui (thread do paho); salva para o connect() tratar
            self._connect_error = CmcMqttAuthError(rc=rc)
            self._connected.set()
            return

        # Subscribe /get/+
        client.subscribe(f"{self.base_topic()}/get/+", qos=0)

        # Opcional: estado online
        try:
            self.publish_set("state", {"state": "1"})
        except Exception:
            pass

        self._connected.set()

    def _on_disconnect(self, client, userdata, rc):
        self._disconnect_rc = rc
        # rc != 0 geralmente indica queda anormal
        self._disconnected.set()

    def _on_message(self, client, userdata, msg):
        topic = msg.topic

        # tenta parsear JSON; se falhar, ignora para não travar
        try:
            payload = self._safe_json_loads(msg.payload)
        except CmcDecodeError:
            return

        # guarda no cache e acorda quem está esperando
        with self._rx_cv:
            self._rx_cache[topic] = payload
            self._rx_cv.notify_all()

        # Eventos obrigatórios do Driver v1.00:

        # Sistema -> Dispositivo: /get/ping  => Dispositivo -> Sistema: /set/pong
        if topic.endswith("/get/ping"):
            try:
                self.publish_set("pong", {"timestamp": now_ts()})
            except Exception:
                pass
            return

        # Sistema -> Dispositivo: /get/state => Dispositivo -> Sistema: /set/state
        if topic.endswith("/get/state"):
            try:
                self.publish_set("state", {"state": "1"})
            except Exception:
                pass
            return

    # -----------------------------
    # Lifecycle
    # -----------------------------
    def connect(self) -> None:
        """
        Conecta ao broker MQTT e aguarda on_connect.

        Converte erros de rede/socket/TLS em exceções próprias da lib.
        """
        self._connected.clear()
        self._disconnected.clear()
        self._disconnect_rc = None
        self._connect_error = None

        client_id = f"{self.cfg.device_addr}-{uuid.uuid4().hex[:8]}"
        self._client = mqtt.Client(client_id=client_id)

        if self.cfg.mqtt_user:
            self._client.username_pw_set(self.cfg.mqtt_user, self.cfg.mqtt_pass)

        # TLS opcional
        if self.tls is not None:
            try:
                self._client.tls_set(
                    ca_certs=self.tls.ca_certs,
                    certfile=self.tls.certfile,
                    keyfile=self.tls.keyfile,
                )
                if self.tls.insecure:
                    self._client.tls_insecure_set(True)
            except ssl.SSLError as e:
                raise CmcTlsError(f"Falha configurando TLS: {e}") from e
            except Exception as e:
                raise CmcTlsError(f"Falha configurando TLS: {e}") from e

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        # Conecta (socket)
        try:
            self._client.connect(
                self.cfg.broker_host,
                int(self.cfg.broker_port),
                keepalive=self.connect_keepalive_s,
            )
        except socket.gaierror as e:
            raise CmcDnsError(f"Hostname inválido ou não resolvido: {self.cfg.broker_host}") from e
        except (TimeoutError, socket.timeout) as e:
            raise CmcConnectionTimeout(
                f"Timeout conectando ao broker MQTT em {self.cfg.broker_host}:{self.cfg.broker_port}. "
                f"Verifique IP/DNS, porta, firewall ou rede."
            ) from e
        except ssl.SSLError as e:
            raise CmcTlsError(f"Erro TLS conectando ao broker: {e}") from e
        except OSError as e:
            raise CmcConnectionError(
                f"Erro de rede conectando ao broker MQTT {self.cfg.broker_host}:{self.cfg.broker_port}: {e}"
            ) from e
        except Exception as e:
            raise CmcMqttProtocolError(f"Erro inesperado conectando MQTT: {e}") from e

        # Loop + aguarda connect callback
        self._client.loop_start()

        if not self._connected.wait(timeout=self.cfg.connect_timeout_s):
            raise CmcConnectionTimeout(
                f"Timeout aguardando CONNACK do broker em {self.cfg.broker_host}:{self.cfg.broker_port}."
            )

        # Se o callback acusou erro (ex: auth)
        if self._connect_error is not None:
            # para limpeza
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
            self._client = None
            raise self._connect_error

    def disconnect(self) -> None:
        if not self._client:
            return

        # tenta offline state
        try:
            self.publish_set("state", {"state": "0"})
            time.sleep(0.2)
        except Exception:
            pass

        try:
            self._client.loop_stop()
        except Exception:
            pass

        try:
            self._client.disconnect()
        except Exception:
            pass

        self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.disconnect()

    # -----------------------------
    # OAuth2 (MQTT+REST)
    # -----------------------------
    def is_token_valid(self) -> bool:
        with self._tok_lock:
            if not self._access_token or not self._token_expiration_ts:
                return False
            return now_ts() < (self._token_expiration_ts - int(self.cfg.token_renew_margin_s))

    def token(self) -> Optional[str]:
        with self._tok_lock:
            return self._access_token

    def login_oauth2(self, timeout_s: Optional[float] = None) -> str:
        """
        Doc (Autenticação / MQTT+REST):
        REQUEST:  .../set/rest/oauth2/login
        RESPONSE: .../get/rest/oauth2/login

        REQUEST payload:
        {
          "request": {
            "headers": { "Authorization": "Basic <base64>" },
            "type": "GET"
          }
        }

        RESPONSE:
        {
          "status":"200",
          "log":"...",
          "access_token":"...",
          "token_type":"Bearer",
          "expires_in":86400
        }
        """
        payload = {
            "request": {
                "headers": {"Authorization": self._api_basic_auth_header()},
                "type": "GET",
            }
        }

        resp = self.request("rest/oauth2/login", payload, timeout_s=timeout_s)

        # status/log padronizado
        self._ensure_status_ok(endpoint="rest/oauth2/login", resp=resp, err_cls=CmcLoginError)

        token = resp.get("access_token")
        if not token:
            raise CmcLoginError(status=str(resp.get("status")), log="Login retornou 200 mas access_token não veio.",
                                endpoint="rest/oauth2/login", raw=resp)

        expires_in = resp.get("expires_in")
        try:
            expires_s = int(expires_in)  # ✅ doc: segundos
        except Exception:
            expires_s = 3600

        with self._tok_lock:
            self._access_token = str(token)
            self._token_expiration_ts = now_ts() + expires_s

        return str(token)

    def ensure_login(self, timeout_s: Optional[float] = None) -> None:
        if self.is_token_valid():
            return
        self.login_oauth2(timeout_s=timeout_s)

    def logout_oauth2(self, timeout_s: Optional[float] = None) -> Dict[str, Any]:
        tok = self.token()
        if not tok:
            return {"status": "200", "log": "Sem token"}

        payload = {
            "request": {
                "headers": {"Authorization": f"Bearer {tok}"},
                "type": "GET",
            }
        }

        resp = self.request("rest/oauth2/logout", payload, timeout_s=timeout_s)

        # logout pode ser best-effort; se quiser validar, descomente:
        # self._ensure_status_ok(endpoint="rest/oauth2/logout", resp=resp, err_cls=CmcApiError)

        # limpa token local
        with self._tok_lock:
            self._access_token = None
            self._token_expiration_ts = None

        return resp

    # -----------------------------
    # REST API v1 via MQTT+REST
    # -----------------------------
    def setup_apontamento(self, setup: SetupApontamento, timeout_s: Optional[float] = None) -> Dict[str, Any]:
        """
        Doc: /api/v1/setup.apontamento via MQTT+REST
        REQUEST:  .../set/rest/api/v1/setup.apontamento
        RESPONSE: .../get/rest/api/v1/setup.apontamento

        MQTT+REST payload:
        {
          "request": {
            "headers": {...},
            "type": "POST",
            "params": {...}   # opcional
          },
          "data": { ... }     # JSON Setup
        }
        """
        if not isinstance(setup, SetupApontamento):
            raise CmcInvalidArgument("setup deve ser um SetupApontamento")

        self.ensure_login(timeout_s=timeout_s)
        tok = self.token()
        if not tok:
            raise CmcLoginError(status="401", log="Token ausente após login.", endpoint="rest/oauth2/login", raw=None)

        payload = {
            "request": {
                "headers": {
                    "Authorization": f"Bearer {tok}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                "type": "POST",
            },
            "data": setup.to_dict(),
        }

        resp = self.request("rest/api/v1/setup.apontamento", payload, timeout_s=timeout_s)

        # valida status e (opcional) erro de negócio via log
        self._ensure_status_ok(endpoint="rest/api/v1/setup.apontamento", resp=resp, err_cls=CmcApontamentoError)
        return resp

    # -----------------------------
    # Helpers de uso (um serial por request)
    # -----------------------------
    def apontar_serial(
        self,
        serial: str,
        *,
        timeout_s: Optional[float] = None,
        evidencias: Optional[list[Evidence]] = None,
    ) -> Dict[str, Any]:
        """
        Apontamento simples serializado (1 serial por request) — recomendado no seu cenário.

        {
          "enderecoDispositivo":"device001",
          "apontamentos":[
            { "ok": true, "seriais":[{"codigo":"..."}] }
          ]
        }
        """
        s = str(serial).strip()
        if not s:
            raise CmcInvalidArgument("serial vazio.")

        ap = Apontamento(ok=True, serial=Serial(codigo=s), evidencias=evidencias or None)
        setup = SetupApontamento(enderecoDispositivo=self.cfg.device_addr, apontamentos=[ap])
        return self.setup_apontamento(setup, timeout_s=timeout_s)

    def validar_rota(self, serial: str, *, timeout_s: Optional[float] = None) -> Dict[str, Any]:
        """
        Usa ciclo VALIDAR_ROTA conforme doc Setup.
        """
        s = str(serial).strip()
        if not s:
            raise CmcInvalidArgument("serial vazio.")

        ap = Apontamento(ok=True, serial=Serial(codigo=s))
        setup = SetupApontamento(
            enderecoDispositivo=self.cfg.device_addr,
            ciclo="VALIDAR_ROTA",
            apontamentos=[ap],
        )
        return self.setup_apontamento(setup, timeout_s=timeout_s)

    def apontar_lote_1porreq(
        self,
        seriais: list[str],
        *,
        timeout_s: Optional[float] = None,
        delay_s: float = 0.2,
        stop_on_error: bool = False,
    ) -> list[Dict[str, Any]]:
        """
        Faz N requests, 1 serial por payload (ideal para seu caso).

        stop_on_error=True: para no primeiro erro de apontamento.
        """
        out: list[Dict[str, Any]] = []
        for x in seriais:
            resp = self.apontar_serial(str(x), timeout_s=timeout_s)
            out.append(resp)

            status = str(resp.get("status", "")).strip() if resp.get("status") is not None else ""
            log = str(resp.get("log") or resp.get("message") or "").strip()

            # Se status != 200, normalmente setup_apontamento já teria levantado exception.
            # Aqui é só redundância/compatibilidade se você desativar validação por status.
            if stop_on_error and status and not status.startswith("200"):
                break

            if delay_s > 0:
                time.sleep(float(delay_s))

        return out