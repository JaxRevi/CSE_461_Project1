import struct

class Header:
    def __init__(self, payload_len, p_secret, step, student_id) -> None:
        """Header object constructor.

        Args:
            payload_len (int): Payload length not including alignment.
            p_secret (int): Previous Stage secret.
            step (int): Current step.
            student_id (int): Student id.
        """
        self._payload_len = payload_len
        self._p_secret = p_secret
        self._step = step
        self._student_id = student_id
    
    def getBytes(self) -> bytes:
        """Converts header fields into bytes. For project 1, header information is 12 bytes long.
        Step and studnet_id get packed into 2 bytes each.

        Returns:
            bytes: Number of bytes for the header.
        """
        return struct.pack('>IIHH', self._payload_len, self._p_secret, self._step, self._student_id)
    
    def getSecret(self) -> int:
        return self._p_secret
    
    def getStep(self) -> int:
        return self._step
    
    def getId(self) -> int:
        return self._student_id
    
    def getSize(self) -> int:
        """Returns the size of header.

        Returns:
            int: Length of bytes in header.
        """
        return len(self.getBytes())