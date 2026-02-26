# pycmcontrol-mqtt

Biblioteca Python para integração com o Driver Dispositivo CmControl v1.00 via MQTT, implementando com base no protocolo oficial do sistema.

A biblioteca encapsula toda a comunicação MQTT + MQTT+REST + OAuth2, permitindo que aplicações Python atuem como um dispositivo CmControl totalmente compatível.

## Recursos

- Comunicação MQTT conforme especificação do Driver v1.00
- Subscrição automática em .../get/#
- Publicação com QoS = 0 e retained = false
- Resposta automática aos eventos obrigatórios:
  - PING → PONG 
  - STATE → envio de estado online 
- Suporte ao proxy MQTT+REST (set/rest/...)
- Autenticação OAuth2 (Basic → Bearer)
- Execução de endpoints REST via MQTT
- Endpoint de apontamento setup.apontamento
- Envio de seriais, evidências e estruturas completas
- Tratamento robusto de erros de rede, MQTT, timeout e negócio
- Cliente context manager (with)
- Debug opcional com log das trocas MQTT
- Tipagem estática (PEP 561 — pacote typed)

## Instalação
```bash
pip install pycmcontrol-mqtt
```
## Uso básico
Configuração e conexão
```python
from pycmcontrol_mqtt import CmControlClient, CmControlConfig

cfg = CmControlConfig(
    device_addr="device001",
    broker_host="cmcontrol.example.com",
    broker_port=1883,
    mqtt_user="usuario",
    mqtt_pass="senha",
    api_user="api_user",
    api_pass="api_pass",
)

with CmControlClient(cfg) as cmc:
    cmc.ensure_login()
```

## Autenticação OAuth2 (MQTT+REST)

A biblioteca executa automaticamente o fluxo:
1. Login BASIC → obtenção de token JWT
2. Uso do token Bearer nas requisições REST via MQTT
```python
with CmControlClient(cfg) as cmc:
    cmc.ensure_login()
```
Logout opcional:
```python
cmc.logout_oauth2()
```
## Eventos obrigatórios do driver

O cliente responde automaticamente quando conectado:

| Evento recebido | Resposta enviada           |
| --------------- | -------------------------- |
| `/get/ping`     | `/set/pong` com timestamp  |
| `/get/state`    | `/set/state {"state":"1"}` |

Também envia `state=1` ao conectar.

## Apontamento simples (serializado)
```python
from pycmcontrol_mqtt import CmControlClient

with CmControlClient(cfg) as cmc:
    cmc.ensure_login()
    resp = cmc.apontar_serial("00000203030300")
    print(resp)
```
Payload equivalente:
```json
{
  "enderecoDispositivo": "device001",
  "apontamentos": [
    {
      "ok": true,
      "seriais": [
        { "codigo": "00000203030300" }
      ]
    }
  ]
}
```
## Apontamento com evidência
Evidência a partir de texto
```python
from pycmcontrol_mqtt import Evidence

evi = Evidence.from_text(
    nome="log_teste",
    extensao="txt",
    texto="Conteúdo da evidência",
    descricao="Log de teste"
)

with CmControlClient(cfg) as cmc:
    cmc.ensure_login()
    cmc.apontar_serial("00000203030300", evidencias=[evi])
```
Evidência a partir de arquivo
```python
evi = Evidence.from_file("foto.png")

cmc.apontar_serial("00000203030300", evidencias=[evi])
```
## Validação de rota
```python
serial = "00000203030300"
resp = cmc.validar_rota(serial)
```
## Apontamento em lote (1 serial por requisição)
```python
seriais = ["001", "002", "003"]

resp = cmc.apontar_lote_1porreq(seriais)
```
# Debug das trocas MQTT

Ative logs detalhados:
```python
with CmControlClient(cfg, debug=True) as cmc:
    cmc.ensure_login()
```
Exemplo de saída:
```terminaloutput
[pycmcontrol] -> SET br/com/cmcontrol/dispositivo/device001/set/rest/oauth2/login
[pycmcontrol] <- GET br/com/cmcontrol/dispositivo/device001/get/rest/oauth2/login status=200 log=OK
```
## Tratamento de erros
A biblioteca fornece exceções específicas:
```python
from pycmcontrol_mqtt.errors import (
    CmcConnectionError,
    CmcLoginError,
    CmcApontamentoError,
    CmcTimeout,
)

try:
    with CmControlClient(cfg) as cmc:
        cmc.ensure_login()
        cmc.apontar_serial("00000203030300")

except CmcConnectionError as e:
    print("Falha de conexão:", e)

except CmcLoginError as e:
    print("Falha de login:", e)

except CmcApontamentoError as e:
    print("Erro de negócio:", e.status, e.log)

except CmcTimeout:
    print("Timeout aguardando resposta")
```
## Inspeção da última troca MQTT

Útil para diagnóstico:
```python
print(cmc.last_exchange())
```
Retorna:
```terminaloutput
{
  "last_request": {...},
  "last_response": {...},
  "disconnect_rc": None
}
```
## Configuração TLS (opcional)

Para brokers MQTT seguros (porta 8883):
```python
from pycmcontrol_mqtt import BrokerTLS

tls = BrokerTLS(
    ca_certs="ca.pem",
    certfile="client.crt",
    keyfile="client.key",
)

with CmControlClient(cfg, tls=tls) as cmc:
    cmc.ensure_login()
```
## Estrutura do pacote
```bash
pycmcontrol_mqtt/
 ├── client.py
 ├── config.py
 ├── models.py
 ├── errors.py
 ├── utils.py
 └── py.typed
```
## Requisitos

- Python ≥ 3.9 
- Broker MQTT compatível com CmControl 
- Dispositivo previamente cadastrado no sistema

## Licença

[MIT License](LICENSE)

## Autor
Marcos Tullio Silva de Souza