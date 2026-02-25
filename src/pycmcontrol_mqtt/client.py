from __future__ import annotations

import json
import threading
import time
import uuid
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from .config import CmControlConfig
from .errors import CmcTimeout, CmcNotConnected, CmcLoginError, CmcRequestError
from .utils import now_ts, b64
from .models import SetupApontamento, Apontamento, Serial, Evidence


class CmControlClient:
    """
    Implementa o Driver Dispositivo CmControl v1.00 + MQTT+REST proxy, conforme documentação.

    Regras da doc:
    - REQUEST: br/com/cmcontrol/dispositivo/{device}/set/{endpoint}
    - RESPONSE: br/com/cmcontrol/dispositivo/{device}/get/{endpoint}
    - QoS = 0
    - Retained = false
    - Dispositivo deve ficar inscrito em: .../get/+
    - Se o sistema enviar /get/ping -> responder /set/pong
    - Se o sistema enviar /get/state -> responder /set/state
    """

    def __init__(self, cfg: CmControlConfig):
        self.cfg = cfg
        self._client: Optional[mqtt.Client] = None
        self._connected = threading.Event()

        # Cache de respostas por tópico (conforme sugestão da doc)
        self._rx_lock = threading.Lock()
        self._rx_cv = threading.Condition(self._rx_lock)
        self._rx_cache: Dict[str, Dict[str, Any]] = {}

        # Token
        self._tok_lock = threading.Lock()
        self._access_token: Optional[str] = None
        self._token_expiration_ts: Optional[int] = None

        # Serializa requests (evita colisão de resposta do mesmo endpoint)
        self._req_lock = threading.Lock()

    # -----------------------------
    # Tópicos
    # -----------------------------
    def base_topic(self) -> str:
        return f"br/com/cmcontrol/dispositivo/{self.cfg.device_addr}"

    def topic_set(self, endpoint: str) -> str:
        return f"{self.base_topic()}/set/{endpoint}"

    def topic_get(self, endpoint: str) -> str:
        return f"{self.base_topic()}/get/{endpoint}"

    # -----------------------------
    # MQTT low-level
    # -----------------------------
    def _ensure_client(self) -> mqtt.Client:
        if not self._client:
            raise CmcNotConnected("Client not connected. Call connect().")
        return self._client

    def publish_set(self, endpoint: str, payload: Any) -> None:
        """
        Publica REQUEST em /set/{endpoint}, com QoS=0 e retained=false.
        """
        c = self._ensure_client()
        c.publish(self.topic_set(endpoint), json.dumps(payload), qos=0, retain=False)

    def request(self, endpoint: str, payload: Any, timeout_s: float = 10.0) -> Dict[str, Any]:
        """
        REQUEST: /set/{endpoint}
        RESPONSE: /get/{endpoint}
        Armazena resposta em cache por tópico e aguarda até timeout.
        """
        resp_topic = self.topic_get(endpoint)

        with self._req_lock:
            # limpa resposta anterior desse endpoint
            with self._rx_cv:
                self._rx_cache.pop(resp_topic, None)

            self.publish_set(endpoint, payload)

            end = time.time() + float(timeout_s)
            with self._rx_cv:
                while True:
                    if resp_topic in self._rx_cache:
                        return self._rx_cache[resp_topic]
                    remaining = end - time.time()
                    if remaining <= 0:
                        raise CmcTimeout(f"Timeout aguardando resposta em {resp_topic}")
                    self._rx_cv.wait(timeout=remaining)

    # -----------------------------
    # Callbacks (Driver v1.00)
    # -----------------------------
    def _on_connect(self, client, userdata, flags, rc):
        self._connected.set()

        # doc sugere: .../get/+
        client.subscribe(f"{self.base_topic()}/get/+", qos=0)

        # opcional: declarar online ao conectar (estado 1)
        self.publish_set("state", {"state": "1"})

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        topic = msg.topic

        # guarda no cache e acorda waiters
        with self._rx_cv:
            self._rx_cache[topic] = payload
            self._rx_cv.notify_all()

        # Eventos exigidos pelo Driver:
        # Sistema -> Dispositivo: /get/ping  => Dispositivo -> Sistema: /set/pong
        if topic.endswith("/get/ping"):
            self.publish_set("pong", {"timestamp": now_ts()})
            return

        # Sistema -> Dispositivo: /get/state => Dispositivo -> Sistema: /set/state
        if topic.endswith("/get/state"):
            self.publish_set("state", {"state": "1"})
            return

    # -----------------------------
    # Lifecycle
    # -----------------------------
    def connect(self) -> None:
        self._connected.clear()

        client_id = f"{self.cfg.device_addr}-{uuid.uuid4().hex[:8]}"
        self._client = mqtt.Client(client_id=client_id)

        if self.cfg.mqtt_user:
            self._client.username_pw_set(self.cfg.mqtt_user, self.cfg.mqtt_pass)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self._client.connect(self.cfg.broker_host, self.cfg.broker_port)
        self._client.loop_start()

        if not self._connected.wait(timeout=self.cfg.connect_timeout_s):
            raise CmcTimeout("Timeout conectando no broker MQTT.")

    def disconnect(self) -> None:
        if not self._client:
            return

        # offline (state=0) apenas se tiver standby; aqui enviamos por boa prática
        try:
            self.publish_set("state", {"state": "0"})
            time.sleep(0.2)
        except Exception:
            pass

        self._client.loop_stop()
        self._client.disconnect()
        self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.disconnect()

    # -----------------------------
    # OAuth2 (MQTT+REST)
    # -----------------------------
    def _basic_auth_header(self) -> str:
        if not self.cfg.has_api_credentials:
            raise CmcLoginError("api_user/api_pass não definidos no config.")
        return f"Basic {b64(f'{self.cfg.api_user}:{self.cfg.api_pass}')}"  # doc: Basic base64(login:senha)

    def is_token_valid(self) -> bool:
        with self._tok_lock:
            if not self._access_token or not self._token_expiration_ts:
                return False
            return now_ts() < (self._token_expiration_ts - self.cfg.token_renew_margin_s)

    def token(self) -> Optional[str]:
        with self._tok_lock:
            return self._access_token

    def login_oauth2(self, timeout_s: float = 10.0) -> str:
        """
        Doc (Autenticação / MQTT+REST):
        REQUEST:  br/com/cmcontrol/dispositivo/{device}/set/rest/oauth2/login
        RESPONSE: br/com/cmcontrol/dispositivo/{device}/get/rest/oauth2/login

        PAYLOAD:
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
                "headers": {
                    "Authorization": self._basic_auth_header()
                },
                "type": "GET"
            }
        }
        resp = self.request("rest/oauth2/login", payload, timeout_s=timeout_s)

        status = str(resp.get("status", "")).strip()
        if status != "200":
            raise CmcLoginError(str(resp.get("log") or resp.get("message") or f"status={status}"))

        token = resp.get("access_token")
        if not token:
            raise CmcLoginError("Login retornou 200 mas não trouxe access_token.")

        expires_in = resp.get("expires_in")
        try:
            expires_s = int(expires_in)
        except Exception:
            expires_s = 3600

        with self._tok_lock:
            self._access_token = token
            self._token_expiration_ts = now_ts() + expires_s  # ✅ segundos

        return token

    def ensure_login(self, timeout_s: float = 10.0) -> None:
        if self.is_token_valid():
            return
        self.login_oauth2(timeout_s=timeout_s)

    def logout_oauth2(self, timeout_s: float = 10.0) -> Dict[str, Any]:
        """
        Doc: /rest/oauth2/logout
        """
        tok = self.token()
        if not tok:
            return {"status": "200", "log": "Sem token"}

        payload = {
            "request": {
                "headers": {"Authorization": f"Bearer {tok}"},
                "type": "GET"
            }
        }
        resp = self.request("rest/oauth2/logout", payload, timeout_s=timeout_s)
        return resp

    # -----------------------------
    # API v1: setup.apontamento (MQTT+REST)
    # -----------------------------
    def setup_apontamento(self, setup: SetupApontamento, timeout_s: float = 10.0) -> Dict[str, Any]:
        """
        Doc: Endpoint /api/v1/setup.apontamento via MQTT+REST:
        REQUEST:  /set/rest/api/v1/setup.apontamento
        RESPONSE: /get/rest/api/v1/setup.apontamento

        MQTT+REST payload (padrão):
        {
          "request": {
            "headers": {...},
            "type": "POST",
            "params": {...}   # opcional
          },
          "data": { ... }     # JSON do Setup
        }
        """
        self.ensure_login(timeout_s=timeout_s)
        tok = self.token()
        if not tok:
            raise CmcLoginError("Token inválido após login.")

        payload = {
            "request": {
                "headers": {
                    "Authorization": f"Bearer {tok}",
                    # Doc REST: POST usa form urlencoded; aqui mantemos explícito:
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                "type": "POST"
            },
            "data": setup.to_dict()
        }

        resp = self.request("rest/api/v1/setup.apontamento", payload, timeout_s=timeout_s)

        # Padrão de respostas REST na doc:
        # { "status":"200", "log":"OK", "data": ... }
        status = str(resp.get("status", "")).strip()
        log = str(resp.get("log", "") or resp.get("message", "") or "").strip()

        if status and status != "200":
            raise CmcRequestError(status=status, log=log)

        return resp

    # -----------------------------
    # Helpers de uso (serial)
    # -----------------------------
    def apontar_lote(self, seriais: list[str], timeout_s: float = 10.0,
                     delay_s: float = 0.2, stop_on_error: bool = False) -> list[Dict[str, Any]]:
        """
            Lote (N requests)
        """
        out = []
        for s in seriais:
            resp = self.apontar_serial(s, timeout_s=timeout_s)
            out.append(resp)
            status = str(resp.get("status", "")).strip()
            if stop_on_error and status != "200":
                break
            if delay_s > 0:
                time.sleep(delay_s)
        return out

    def apontar_vinculacao(self, serial_a: str, serial_b: str, timeout_s: float = 10.0) -> Dict[str, Any]:
        ap = Apontamento(ok=True, seriais_vinculados=[
            Serial(codigo=str(serial_a).strip()),
            Serial(codigo=str(serial_b).strip()),
        ])
        setup = SetupApontamento(enderecoDispositivo=self.cfg.device_addr, apontamentos=[ap])
        return self.setup_apontamento(setup, timeout_s=timeout_s)

    def validar_rota(self, serial: str, timeout_s: float = 10.0) -> Dict[str, Any]:
        """
        Usa 'ciclo': VALIDAR_ROTA (doc Setup -> ciclo).
        """
        ap = Apontamento(ok=True, seriais=[Serial(codigo=str(serial).strip())])
        setup = SetupApontamento(
            enderecoDispositivo=self.cfg.device_addr,
            ciclo="VALIDAR_ROTA",
            apontamentos=[ap]
        )
        return self.setup_apontamento(setup, timeout_s=timeout_s)