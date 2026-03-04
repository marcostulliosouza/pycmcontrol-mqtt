pycmcontrol-mqtt
================
.. image:: https://img.shields.io/pypi/v/pycmcontrol-mqtt.svg
    :target: https://pypi.org/project/pycmcontrol-mqtt/
    :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/pycmcontrol-mqtt.svg
    :alt: Python Versions

.. image:: https://static.pepy.tech/personalized-badge/pycmcontrol-mqtt?period=total&units=international_system&left_color=black&right_color=green&left_text=downloads
    :target: https://pepy.tech/projects/pycmcontrol-mqtt
    :alt: Downloads

**Versão:** 1.0.0
**Licença:** MIT
**Python:** 3.8+

Biblioteca Python para integração com o **Driver Dispositivo CmControl v1.00** via MQTT,
implementando o protocolo oficial do sistema.

Permite que aplicações Python atuem como um dispositivo CmControl totalmente compatível,
suportando:

- Comunicação MQTT nativa
- Proxy MQTT + REST
- Autenticação OAuth2
- Apontamento de seriais
- Envio de evidências
- TLS
- Tipagem estática (PEP 561)

.. toctree::
   :maxdepth: 2
   :caption: Conteúdo

   installation
   quickstart
   oauth2
   mqtt
   apontamento
   errors
   tls
   api
   structure

.. toctree::
   :maxdepth: 1
   :caption: Links Úteis
   :hidden:

   GitHub <https://github.com/marcostulliosouza/pycmcontrol-mqtt>
   PyPI <https://pypi.org/project/pycmcontrol-mqtt/>
   Issue Tracker <https://github.com/marcostulliosouza/pycmcontrol-mqtt/issues>