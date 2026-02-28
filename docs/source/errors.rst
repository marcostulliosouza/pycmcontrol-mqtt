Tratamento de Erros
===================

Exceções disponíveis:

- CmcConnectionError
- CmcLoginError
- CmcApontamentoError
- CmcTimeout

Exemplo:

.. code-block:: python

   from pycmcontrol_mqtt.errors import (
       CmcConnectionError,
       CmcLoginError,
       CmcApontamentoError,
       CmcTimeout,
   )