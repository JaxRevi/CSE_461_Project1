import struct

class Header:
    def __init__(self, payload_len, p_secret, step, student_id):
        self._payload_len = payload_len
        self._p_secret = p_secret
        self._step = step
        self._student_id = student_id
    
    def getBytes(self):
        return struct.pack('>iihh', self._payload_len, self._p_secret, self._step, self._student_id)
    