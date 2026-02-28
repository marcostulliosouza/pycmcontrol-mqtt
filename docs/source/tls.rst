TLS
===

Para brokers seguros (porta 8883):

.. code-block:: python

   from pycmcontrol_mqtt import BrokerTLS

   tls = BrokerTLS(
       ca_certs="ca.pem",
       certfile="client.crt",
       keyfile="client.key",
   )

   with CmControlClient(cfg, tls=tls) as cmc:
       cmc.ensure_login()