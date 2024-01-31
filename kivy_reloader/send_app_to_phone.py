import trio
from colorama import Fore, Style, init

try:
    from settings import PHONE_IPS
except:
    from constants import PHONE_IPS

red = Fore.RED
green = Fore.GREEN
yellow = Fore.YELLOW
white = Fore.WHITE
init(autoreset=True)


async def connect_to_server(IP):
    try:
        PORT = 8050
        print(f"Connecting to IP: {green}{IP}{white} and PORT: {green}{PORT}")
        with trio.move_on_after(1):
            client_socket = await trio.open_tcp_stream(IP, PORT)
            return client_socket
    except Exception as e:
        print(f"{red}Error: {e}")
        return None


async def send_app():
    print("*" * 50)
    print(green + "Connecting to smartphone...")
    count = 0
    total_desconnected = 0
    try:
        for IP in PHONE_IPS[count:]:
            count += 1
            client_socket = await connect_to_server(IP)
            if not client_socket:
                total_desconnected += 1
                print(yellow + f"Couldn't connect to smartphone: {IP}\n")
                continue
            print(yellow + f"Phone connected successfully: ", IP)
            print(f"\n{green}Sending app to smartphone...")
            CHUNK_SIZE = 4096
            with open(
                "app_copy.zip",
                "rb",
            ) as myzip:
                for chunk in iter(lambda: myzip.read(CHUNK_SIZE), b""):
                    print("Sending chunk")
                    await client_socket.send_all(chunk)
            print(green + "Finished sending app!")
        print("\n")
        print(yellow + f"Sent app to {len(PHONE_IPS) - total_desconnected} smartphone(s)")
        print("*" * 50)
    except:
        pass


trio.run(send_app)
