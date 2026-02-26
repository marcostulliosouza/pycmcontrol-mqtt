# pycmcontrol-mqtt

Biblioteca Python para integração com o **Driver Dispositivo CmControl v1.00** via MQTT, implementando o protocolo oficial do sistema.

Permite que aplicações Python atuem como um dispositivo CmControl totalmente compatível, suportando comunicação MQTT nativa, proxy MQTT+REST e autenticação OAuth2.

---

## Recursos

* Comunicação MQTT conforme especificação oficial do driver
* Subscrição automática em `.../get/#`
* Publicação com QoS = 0 e retained = false
* Handlers automáticos obrigatórios:

  * PING → PONG
  * STATE → status online
* Suporte completo ao proxy MQTT+REST
* Autenticação OAuth2 (Basic → Bearer JWT)
* Execução de endpoints REST via MQTT
* Apontamentos (`setup.apontamento`)
* Envio de seriais e evidências
* Tratamento robusto de erros de rede e negócio
* Cliente context manager (`with`)
* Debug detalhado opcional
* Tipagem estática (PEP 561)
* Compatível com TLS

---

## Instalação

```bash
pip install pycmcontrol-mqtt
```

---

## Uso rápido

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

with CmControlClient(cfg, debug=True) as cmc:
    cmc.ensure_login()
```

---

## Autenticação OAuth2 (MQTT+REST)

O cliente executa automaticamente:

1. Login BASIC
2. Recebimento de token JWT
3. Uso de Bearer Token nas chamadas REST

```python
with CmControlClient(cfg) as cmc:
    cmc.ensure_login()
```

Logout opcional:

```python
cmc.logout_oauth2()
```

---

## 📡 Eventos obrigatórios do driver

Quando conectado, o cliente responde automaticamente:

| Evento recebido | Resposta enviada           |
| --------------- | -------------------------- |
| `/get/ping`     | `/set/pong` com timestamp  |
| `/get/state`    | `/set/state {"state":"1"}` |

Também envia `state=1` ao conectar.

---

## O que você pode fazer com CmControlClient

### Ciclo de vida

Criação do cliente (sem conectar):

```python
cmc = CmControlClient(cfg, debug=True)
```

Opções importantes:

* `debug=True` → log detalhado de trocas MQTT
* `request_timeout_s_default` → timeout padrão
* `strict_business_errors` → transforma erros de negócio em exceção

---

### Conexão

* `connect()` → conecta e envia `state=1`
* `disconnect()` → envia `state=0` e desconecta

Uso recomendado com context manager:

```python
with CmControlClient(cfg) as cmc:
    ...
```

---

### Comunicação MQTT direta

* `publish_set(endpoint, payload)`
* `request(endpoint, payload, timeout_s=None)`
* `ping(timeout_s=None)`

Implementa o padrão RPC do driver:

```
SET → GET correspondente
```

---

### OAuth2

* `login_oauth2()`
* `ensure_login()`
* `logout_oauth2()`
* `token()`
* `is_token_valid()`

---

### Apontamento

* `setup_apontamento(setup)`
* `apontar_serial(serial, evidencias=None)`
* `validar_rota(serial)`
* `apontar_lote_1porreq(seriais)`

---

### Debug e diagnóstico

```python
print(cmc.last_exchange())
```

Retorna a última troca MQTT completa.

---

## Apontamento simples

```python
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

---

## Apontamento com evidência

### Evidência a partir de texto

```python
from pycmcontrol_mqtt import Evidence

evi = Evidence.from_text(
    nome="log_teste",
    extensao="txt",
    texto="Conteúdo da evidência",
    descricao="Log de teste"
)

cmc.apontar_serial("00000203030300", evidencias=[evi])
```

### Evidência a partir de arquivo

```python
evi = Evidence.from_file("foto.png")

cmc.apontar_serial("00000203030300", evidencias=[evi])
```

---

## Validação de rota

```python
resp = cmc.validar_rota("00000203030300")
```

---

## Apontamento em lote

Um serial por requisição:

```python
seriais = ["001", "002", "003"]

cmc.apontar_lote_1porreq(seriais)
```

---

## Debug detalhado

Ative logs de comunicação:

```python
with CmControlClient(cfg, debug=True) as cmc:
    cmc.ensure_login()
```

Exemplo:

```
[pycmcontrol] -> SET .../set/rest/oauth2/login
[pycmcontrol] <- GET .../get/rest/oauth2/login status=200 log=OK
```

---

## Tratamento de erros

Exceções específicas:

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

---

## Inspeção da última troca MQTT

```python
print(cmc.last_exchange())
```

Retorno:

```bash
{
  "last_request": {...},
  "last_response": {...},
  "disconnect_rc": None
}
```

---

## TLS (opcional)

Para brokers seguros (porta 8883):

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

---

## Estrutura do pacote

```bash
pycmcontrol_mqtt/
 ├── client.py
 ├── config.py
 ├── models.py
 ├── errors.py
 └── utils.py
```

---

## Requisitos

* Python ≥ 3.9
* Broker MQTT compatível com CmControl
* Dispositivo previamente cadastrado no sistema

---

## Licença

Distribuído sob licença MIT. Acesse [LICENSE](LICENSE) para mais informações.

---

## Autor

**Marcos Tullio Silva de Souza**
