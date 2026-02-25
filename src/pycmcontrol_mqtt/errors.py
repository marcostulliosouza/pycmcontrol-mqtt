class CmcError(Exception):
    """Erro base da biblioteca."""
    pass


class CmcTimeout(CmcError):
    pass


class CmcNotConnected(CmcError):
    pass


class CmcLoginError(CmcError):
    pass


class CmcRequestError(CmcError):
    """Erro quando o CmControl retorna status != 200."""
    def __init__(self, status: str, log: str):
        super().__init__(f"status={status} log={log}")
        self.status = status
        self.log = log