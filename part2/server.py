class Server:
    def __init__(self, server_address="localhost", port=12235, byte_align=4) -> None:
        """Server constructor

        Args:
            server_address (str, optional): Server address that this server object should bind to. Defaults to 'localhost'.
            port (int, optional): Port that this server should listen on. Defaults to 12235.
            byte_align (int, optional): Byte alignment for system. Defaults to 4.
        """
        self._server_address = server_address
        self._default_port = port
        self._read_size = 1024
        self._lower_port = 49152
        self._upper_port = 65535
        self._byte_align = byte_align
        self._student_id = 246
        self.main_socket = None

    def getId(self) -> int:
        return self._student_id

    def getPort(self) -> int:
        return self._default_port

    def getAddress(self) -> str:
        return self._server_address

    def getByteAlign(self) -> int:
        return self._byte_align

    def getReadSize(self) -> int:
        return self._read_size

    def getLowerPort(self) -> int:
        return self._lower_port

    def getUpperPort(self) -> int:
        return self._upper_port
