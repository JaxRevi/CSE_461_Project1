import socket
import struct
import random
import threading
from server import Server
from header import Header


def start(server_address="localhost", default_port=12235) -> None:
    """Start function that creates server object that will handle client requests.

    Args:
        server_address (str, optional): Server address. Defaults to 'localhost'.
        default_port (int, optional): Port that server should listen on. Defaults to 12235.
    """

    # create server object
    server = Server(server_address, default_port)

    print("Server setup...")
    print("Listening for client requests...")

    # this socket will listen for client inital request and
    # create a thread once it receives a request
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_address, default_port))

    # wait for new requests, terminate after timer goes off.
    server_socket.settimeout(30)

    while True:
        try:
            message, client_address = server_socket.recvfrom(server.getReadSize())
            client_handler = threading.Thread(
                target=stageA,
                args=(
                    server,
                    message,
                    client_address,
                ),
            )
            client_handler.start()
            server_socket.settimeout(30)
        except socket.timeout:
            print("Have not received client request for 30 seconds..")
            print("Shutting down.")
            server_socket.close()
            exit()


def validateHeader(server, id: int, step: int) -> bool:
    """Function to validate student id and step in client header.

    Args:
        server (Server): server object to check id and step on
        id (int): client student to validate
        step (int): client step to validate

    Returns:
        bool: returns True if stduent id and step match expected values
    """

    if server.getId() != id:
        print(f"Mismatch student ID, got {id} expected {server.getId()}.")
        return False
    # client always sends a header with step == 1
    elif step != 1:
        print("Wrong client step number.")
        return False
    return True


def calculateAligndLength(byte_align: int, length: int) -> int:
    """Function that calucates the correct byte alignement needed.

    Args:
        byte_align (int): Byte alignment
        length (int): Length to align

    Returns:
        int: The new length after alignment.
    """

    return length + ((byte_align - length % byte_align) % byte_align)


def stageA(server, message, client_address) -> None:
    """Handles server logic for project 1

    Args:
        server (Server): Server object.
        message (bytes): Inital byte message from client.
        client_address (_RetAddress): Client return address.
    """

    # unpack client inital message.
    header_length = 12
    payload_len, p_secret, step, student_id = struct.unpack(
        ">IIHH", message[:header_length]
    )
    client_payload = message[header_length : header_length + payload_len]

    print("Validating client response for Stage A.")
    hello_world = "hello world\0"
    aligned_payload_len = calculateAligndLength(server.getByteAlign(), len(hello_world))

    if not validateHeader(server, student_id, step):
        print("Invalid header in StageA...")
        return
    elif client_payload != hello_world.encode():
        print(
            f"Wrong payload for stage A, was {client_payload.decode()} but expected {hello_world}..."
        )
        return
    elif len(message) != header_length + aligned_payload_len:
        print(
            f"Message length mismatch, was {len(message)} but expected {header_length + aligned_payload_len}..."
        )
        return
    # stage A secret is always 0
    elif p_secret != 0:
        print("Secret mismatch in Stage A...")
        return

    # passed validations
    print("Validation complete. Sending server response.\n")

    # create header to send to client
    # payload length to send contains num, length, udp_port, and secret
    # step in stageA is 0, increments onward
    header = Header(16, p_secret, step=0, student_id=student_id)

    # generate random packet to send to client
    num = random.randint(8, 32)
    length = random.randint(32, 128)
    udp_port = random.randint(server.getLowerPort(), server.getUpperPort())
    secret = random.randint(1, 10000)

    response_payload = struct.pack(">IIII", num, length, udp_port, secret)
    response_message = header.getBytes() + response_payload

    # create socket to send message to client and close socket after
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.sendto(response_message, client_address)
    udp_socket.close()

    # only move onto stage B if passed all validations
    stageB(server, response_payload)


def stageB(server, message) -> None:
    """Server logic for Stage B.

    Args:
        server (Server): Server object.
        message (bytes): Byte payload sent to client in stage A.
    """
    # unpack message sent to client in stage A minus header
    num, length, udp_port, secretB = struct.unpack(">IIII", message)

    # create a socket at udp_port given to client
    # server should close any socket connection if it fails to receive any
    # message from client for more than 3 seconds
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((server.getAddress(), udp_port))
    udp_socket.settimeout(3)

    print(f"Listening for {num} messages from client in StageB...")
    ack = 0
    header_length = 16
    expected_length = header_length + calculateAligndLength(
        server.getByteAlign(), length
    )
    while ack < num:
        # listen for client response
        try:
            response, client_address = udp_socket.recvfrom(server.getReadSize())
        except socket.timeout:
            print("Server timed out in Stage B. Try Again...")
            udp_socket.close()
            return

        # get header info plus client ack number
        payload_length, p_secret, step, student_id, ack_num = struct.unpack(
            ">IIHHI", response[:header_length]
        )
        # get payload of zeros of length payload_length
        payload = response[header_length : header_length + payload_length - 4]
        # construct expected payload
        expected_payload = b"\0" * length

        # validate response
        if not validateHeader(server, student_id, step):
            print("Invalid header in StageB...")
            return
        elif p_secret != secretB:
            print("Incorrent secret from previous stage...")
            return
        elif len(response) != expected_length:
            print(
                f"Message length mismatch, expected {expected_length} but got {len(response)} in Stage B..."
            )
            return
        elif length + 4 != payload_length:
            print(
                f"Payload length mismatch, expected {length + 4} but got {payload_length}"
            )
            return
        elif expected_payload != payload:
            print(
                f"Payload mismatch in Stage B. Expected \n{expected_payload}\n but got \n{payload}\n"
            )
            return
        elif ack < ack_num:
            print(
                "Received a message with a higher acknowledge number then expected..."
            )
            return
        elif ack > ack_num:
            # received an old message, continue and listen for a new message
            continue

        # valided response, send ack message to client to get next message
        # server randomly decides to send an ack packet to client
        if random.randint(0, 1):
            # server decided to send an ack packet
            message = struct.pack(">IIHHI", 4, p_secret, 1, student_id, ack)
            udp_socket.sendto(message, client_address)

            # increment ack number and listen for next message
            ack = ack + 1

    print(f"Received {num} messages from client in Stage B.")
    print("Sending server response.\n")

    # build message for stage C
    tcp_port = random.randint(server.getLowerPort(), server.getUpperPort())
    secretC = random.randint(1, 10000)

    header = Header(8, p_secret, step=1, student_id=server.getId())
    message = header.getBytes() + struct.pack(">II", tcp_port, secretC)

    # setup TCP socket for stageC
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((server.getAddress(), tcp_port))
    tcp_socket.settimeout(3)

    # send client message
    udp_socket.sendto(message, client_address)
    udp_socket.close()
    stageC(server, tcp_socket, secretC)


def stageC(server, tcp_socket: socket.socket, secretC: int) -> None:
    """Server logic for Stage C.

    Args:
        server (Server): Server object.
        tcp_socket (Socket.socket): TCP socket created in stage B. Socket is binded to the TCP port given to client.
        secretC (int): Secret created in Stage B.
    """
    # listen for incoming connections
    print("Server listening for client in Stage C...")
    tcp_socket.listen()

    # try to connect
    try:
        client_socket, client_address = tcp_socket.accept()
    except socket.timeout:
        print("Server timed out waiting for client in Stage C...")
        return

    print("Successfully connected to client in StageC.")
    print("Sending server response.\n")

    # build header and payload for stage D
    header = Header(13, secretC, step=2, student_id=server.getId())
    num2 = random.randint(8, 32)
    length2 = random.randint(32, 128)
    secret = random.randint(1, 10000)
    random_char = chr(random.randint(ord("a"), ord("z")))
    payload = struct.pack(">III", num2, length2, secret) + random_char.encode()
    message = header.getBytes() + payload

    client_socket.sendto(message, client_address)
    stageD(server, tcp_socket, client_socket, client_address, payload)


def stageD(
    server,
    tcp_socket: socket.socket,
    client_socket: socket.socket,
    client_address,
    payload,
) -> None:
    """Server logic for Stage D.

    Args:
        server (Server): Server object.
        tcp_socket (socket.socket): TCP socket created in Stage B.
        client_socket (socket.socket): Client socket that made a connection to TCP socket in Stage C.
        client_address (_RetAddress): Client return address.
        payload (bytes): Payload byte message sent to client in Stage C.
    """

    # unpack message sent to client in stage D.
    num2, length2, secretC, char = struct.unpack(">IIIc", payload)

    # setup expected data
    ack = 0
    header_length = 12
    expected_length = calculateAligndLength(server.getByteAlign(), length2)
    expected_payload = char * length2
    read_size = header_length + expected_length

    # need to receive num valid messages from client
    print(f"Listening for {num2} messages from client in Stage D...")
    while ack < num2:
        # have a chance to read stacked data from client.
        # only read what is expected at one time
        # leave the rest in the buffer to read later.
        try:
            response = client_socket.recv(read_size)
        except socket.timeout:
            print(f"Socket timed out waiting for {num2} messages from client...")
            client_socket.close()
            tcp_socket.close()
            return
        # unpack client response
        payload_len, p_secret, step, student_id = struct.unpack(
            ">IIHH", response[:header_length]
        )
        client_payload = response[header_length : header_length + payload_len]

        # validate client message
        if not validateHeader(server, student_id, step):
            print("Invalid header in Stage D.")
            return
        elif p_secret != secretC:
            print("Secret mismatch in Stage D.")
            return
        elif payload_len != length2:
            print("Payload length mismatch in Stage D.")
            return
        elif expected_payload != client_payload:
            print(
                f"Payload mismatch, expected \n{expected_payload}\n but got \n{client_payload}\n..."
            )
            return
        elif len(response) != header_length + expected_length:
            print(
                f"Message length mismatch, expected {header_length + expected_length} got {len(response)}"
            )
            return

        # successful validation
        # increment ack number
        ack = ack + 1
    print(f"Successfully validated {num2} messages.")
    print("Sending response message.\n")

    # generate final secret message
    header = Header(4, secretC, step=3, student_id=server.getId())
    secret = random.randint(1, 10000)
    message = header.getBytes() + struct.pack(">I", secret)

    client_socket.sendto(message, client_address)

    # TODO: should we wait for client to receive message before closing socket?
    # print("Final secret ", secret)
    client_socket.close()
    tcp_socket.close()


if __name__ == "__main__":
    start()
