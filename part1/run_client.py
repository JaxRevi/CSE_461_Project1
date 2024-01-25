import socket
import struct
from header import Header
from client import Client


def start(server_address="localhost", port=12235) -> None:
    """Driver function that creates an instance of client and
    sends requests to server for project 1.

    Args:
        server_address (str, optional): Server address where client will send requests to. Defaults to "localhost".
        port (int, optional): Port to make intial request to server. Defaults to 12235.
    """
    # create instance of client
    client = Client(server_address, port)

    # Move to stage A and down to later stages.
    stageA(client)
    # print("Finished all Client request.")


def calculateAligndLength(byte_align: int, length: int) -> int:
    """Function that calucates the correct byte alignement needed.

    Args:
        byte_align (int): Byte alignment
        length (int): Length to align

    Returns:
        int: The new length after alignment.
    """

    return length + ((byte_align - length % byte_align) % byte_align)


def alignString(byte_align: int, s: str) -> bytes:
    """Function that aligns string with correct byte alignment.

    Args:
        s (str): String to align.

    Returns:
        bytes: new string with correct padding appended.
    """
    length = len(s)
    padding = (byte_align - length % byte_align) % byte_align
    format_str = f"{length}s{padding}x"
    return struct.pack(format_str, s)


def stageA(client) -> None:
    """Logic for client in Stage A.

    Args:
        client (Client): Client object.

    """
    # create a UDP socket to make intial request.
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(5)

    # create stage A payload.
    payload = alignString(client.getByteAlign(), "hello world\0".encode())
    header = Header(len(payload), client.getSecret(), client.getStep(), client.getId())

    message = header.getBytes() + payload
    print("Sending message to server for stage A.")
    udp_socket.sendto(message, (client.getServerAddress(), client.getPort()))

    # try to read from server
    try:
        response = udp_socket.recv(client.getReadSize())
    except socket.timeout:
        print("Client socket timed out in stage A...")
        return

    # unpack server response minus the header
    num, length, udp_port, secret = struct.unpack(">IIII", response[12:])

    # save necessary data
    client.setSecret(secret)
    client.setPort(udp_port)

    # close no longer needed UDP socket.
    udp_socket.close()

    print(f"Stage A secret is {secret}\n")

    # start Stage B with num and length received from server.
    stageB(client, (num, length))


def stageB(client, stageA_response) -> None:
    """Client logic for Stage B.

    Args:
        stageA_response ((int, int)): Stage A response containing num and length information.
    """

    num, length = stageA_response

    # create a UDP socket to listen on new port number received from
    # server in Stage A. Set socket timer to .5 sec
    upd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    upd_socket.settimeout(0.5)
    port = client.getPort()

    # get aligned payload length.
    aligned_payload_len = calculateAligndLength(client.getByteAlign(), length)

    # create header and payload message for Stage B.
    header = Header(length + 4, client.getSecret(), client.getStep(), client.getId())
    payload = b"\0" * aligned_payload_len

    ack = 0
    # set a max timeout attempts when sending messages to server.
    MAX_TIMEOUTS = 100
    # send num packets to the server on udp_port
    print(f"Sending {num} messages to server for stage B...")
    while ack < num:
        message = header.getBytes() + struct.pack(">I", ack) + payload
        upd_socket.sendto(message, (client.getServerAddress(), port))

        # resend if timeout
        try:
            upd_socket.recv(client.getReadSize())
        except socket.timeout:
            MAX_TIMEOUTS = MAX_TIMEOUTS - 1
            if MAX_TIMEOUTS == 0:
                print("Client socket timed out 100 times in Stage B, check server...")
                return
            continue

        # successfully got a response
        ack = ack + 1

    print("Done sending messages for stage B...")
    # get new message from server containing Stage B secret.
    response = upd_socket.recv(client.getReadSize())

    # unpack message minus header
    tcp_port, secret = struct.unpack(">II", response[len(header.getBytes()) :])

    client.setPort(tcp_port)
    client.setSecret(secret)

    print(f"Stage B secret is {secret}\n")
    upd_socket.close()
    stageC(client)


def stageC(client) -> None:
    """Client logic for Stage C.

    Args:
        client (Client): client object.
    """

    # create a TCP socket that will make a connection to the server socket
    # on port number received in Stage B
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.settimeout(5)
    # create a connection on the tcp port
    try:
        print(f"Connecting to TCP port {client.getPort()} in stage C...")
        tcp_socket.connect((client.getServerAddress(), client.getPort()))
        print("Connect successful.")
    except socket.error as e:
        print("Client socket could not connect in Stage C.")
        print(e)
        return

    # listen for response from server
    try:
        response = tcp_socket.recv(client.getReadSize())
    except socket.timeout:
        print("Did not hear back from server in stage C...")
        return

    # unpack response minus header.
    num2, length2, secret, c = struct.unpack(">IIIc", response[12:25])

    print(f"Stage C secret is {secret}\n")

    client.setSecret(secret)
    stageD(client, tcp_socket, (num2, length2, c))


def stageD(client, tcp_socket, stageC_response) -> None:
    """Client logic for Stage D.

    Args:
        client (Client): Client object.
        tcp_socket (socket.socket): TCP socket created in Stage C.
        stageC_response ((int, int, byte)): Stage C server response containing
        information num2, lenght2, and byte c
    """
    num, length, c = stageC_response

    # create header and payload for stage D
    header = Header(length, client.getSecret(), client.getStep(), client.getId())
    aligned_payload_len = calculateAligndLength(client.getByteAlign(), length)
    payload = c * aligned_payload_len

    message = header.getBytes() + payload

    print(f"Sending {num} number of packets to server in stage D...")
    for _ in range(num):
        tcp_socket.send(message)

    # get response from server
    try:
        response = tcp_socket.recv(client.getReadSize())
    except socket.timeout:
        print("Did not hear back from server in stage D...")
        return

    # get secret from stage D
    _, _, _, _, secret = struct.unpack(">IIHHI", response)
    print(f"Stage D secret is {secret}\n")

    client.setSecret(secret)
    tcp_socket.close()


if __name__ == "__main__":
    start(server_address="attu2.cs.washington.edu")
