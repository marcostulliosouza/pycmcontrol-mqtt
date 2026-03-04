# pycmcontrol-mqtt

[![PyPI version](https://img.shields.io/pypi/v/pycmcontrol-mqtt.svg)](https://pypi.org/project/pycmcontrol-mqtt/)
[![Python versions](https://img.shields.io/pypi/pyversions/pycmcontrol-mqtt.svg)](https://pypi.org/project/pycmcontrol-mqtt/)
[![Downloads](https://static.pepy.tech/personalized-badge/pycmcontrol-mqtt?period=total&units=international_system&left_color=black&right_color=green&left_text=downloads)](https://pepy.tech/projects/pycmcontrol-mqtt)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue)](https://pycmcontrol-mqtt.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Biblioteca Python para integração com o **Driver Dispositivo CmControl v1.00** via MQTT, implementando o protocolo oficial do sistema.

## Documentação

**A documentação completa está disponível em:**  
**[https://pycmcontrol-mqtt.readthedocs.io/](https://pycmcontrol-mqtt.readthedocs.io/)**

## Visão Geral

A biblioteca permite que aplicações Python atuem como um dispositivo CmControl totalmente compatível, suportando:

-  Comunicação MQTT nativa conforme especificação oficial
-  Proxy MQTT + REST com autenticação OAuth2
-  Apontamento de seriais com envio de evidências
-  Handlers automáticos para PING e STATE
-  Tipagem estática (PEP 561)
-  Suporte a TLS
-  Context manager para gerenciamento automático
-  Tratamento robusto de erros

## Instalação Rápida

```bash
pip install pycmcontrol-mqtt
```
## Exemplo Mínimo
```python
from pycmcontrol_mqtt import CmControlClient, CmControlConfig

# Configuração básica
cfg = CmControlConfig(
    device_addr="device001",           # Identificador do dispositivo
    broker_host="cmcontrolbroker.exemplo.com",  # Host do broker MQTT
    broker_port=1883,                   # Porta do broker
    mqtt_user="usuario",                 # Usuário MQTT
    mqtt_pass="senha",                   # Senha MQTT
    api_user="api_user",                 # Usuário para OAuth2
    api_pass="api_pass",                  # Senha para OAuth2
)

# Uso com context manager (conexão automática)
with CmControlClient(cfg) as cmc:
    # Login OAuth2 automático
    cmc.ensure_login()
    
    # Apontamento de serial
    resultado = cmc.apontar_serial("00000203030300")
    print(f"Resultado: {resultado}")
```
## Pré-requisitos

- Python ≥ 3.8
- Broker MQTT compatível com CmControl
- Dispositivo previamente cadastrado no sistema CmControl

## Estrutura do Pacote
```bash
pycmcontrol_mqtt/
 ├── __init__.py        # Inicializador do pacote
 ├── client.py          # Cliente principal (CmControlClient)
 ├── config.py          # Configurações (CmControlConfig, BrokerTLS)
 ├── models.py          # Modelos de dados (Evidence, ApontamentoResponse)
 ├── errors.py          # Exceções específicas (CmcConnectionError, CmcLoginError, ...)
 └── utils.py           # Utilitários internos
```
## Licença

Distribuído sob licença MIT. Acesse [LICENSE](LICENSE) para mais informações.

---

## Autor

**Marcos Tullio Silva de Souza**
