class Client:
    def __init__(self, server_address, default_port, byte_align=4):
        self._server_address = server_address
        self._port = default_port
        self._read_size = 1024
        self._byte_align = byte_align
        self._p_secret = 0
        self._step = 1
        self._student_id = 246

    def getSecret(self) -> int:
        return self._p_secret

    def getStep(self) -> int:
        return self._step

    def getId(self) -> int:
        return self._student_id

    def getPort(self) -> int:
        return self._port

    def getServerAddress(self) -> str:
        return self._server_address

    def getReadSize(self) -> int:
        return self._read_size

    def getByteAlign(self) -> int:
        return self._byte_align

    def setSecret(self, secret: int):
        self._p_secret = secret

    def setPort(self, port: int) -> None:
        self._port = port
