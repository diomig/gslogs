import socket
import subprocess
import time

from colorama import Fore, Style

help_msg = """
=============================================
\033[1mPROMPT          FUNCTION\033[0m
b, beacon       mark any beacon
s, short        mark short beacon
l, long         mark long beacon
a, afsk         mark AFSK messages
p, ping         mark ping and its response
d, drill        check values (not saved to log)
c, comment      add a comment/note
n, note         add a comment/note
t, time         print current time stamp
h, help         this message
q, quit         exit program and save log
q!, j, jump     exit without saving
=============================================
"""


class Rotator:
    def __init__(self, model, addr, port):
        self.model = model
        self.addr = addr
        self.port = port

        self.start()
        time.sleep(1)
        # input()
        self.open_socket()

    def start(self):
        self.daemon = subprocess.Popen(
            f"rotctld -m {self.model} -T {self.addr} -t {self.port}".split()
        )

    def terminate(self):
        self.socket.close()
        self.daemon.terminate()
        self.daemon.wait()

    def open_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.addr, self.port))

    def get_position(self):
        self.socket.send("p\x0a".encode())
        return self.socket.recv(20).decode()


class Rig:
    def __init__(self, model, addr, port):
        self.model = model
        self.addr = addr
        self.port = port

        self.start()
        time.sleep(1)
        # input()
        self.open_socket()

    def start(self):
        self.daemon = subprocess.Popen(
            f"rigctld -m {self.model} -T {self.addr} -t {self.port}".split()
        )

    def terminate(self):
        self.socket.close()
        self.daemon.terminate()
        self.daemon.wait()

    def open_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.addr, self.port))

    def get_freq(self):
        self.socket.send("f\x0a".encode())
        return self.socket.recv(20).decode().split()[0]


def current_time():
    return time.strftime("%H:%M:%S", time.localtime())


def log_time(init_time):
    return time.strftime("%M:%S", time.localtime(time.time() - init_time))


def next_msg(last, period):
    if last == 0:
        return "--:--"
    remaining = last + period - time.time()
    if remaining < 0:
        return f"""{Fore.RED}... [lost signal]{Style.RESET_ALL} \
try {time.strftime('%M:%S', time.localtime(remaining%period))}"""
    return time.strftime("%M:%S", time.localtime(remaining))


def get_comment():
    return input("Comment: ")


def test_setup():
    return input(f"\n{Fore.YELLOW}Test Setup: {Style.RESET_ALL}")


log = []

last_beacon = 0
last_afsk = 0
beacon_period = 60
afsk_period = 120


print(help_msg)
rot = Rotator(1, "localhost", 4533)
print("ROT initialized")
rig = Rig(1, "localhost", 4532)
print("RIG initialized")


log.append(f"\nTest Setup: {test_setup()}\n")

input(Fore.BLUE + "\nPress [ENTER] to start log session" + Style.RESET_ALL)
init_time = time.time()

st_str = f"Start time: {current_time()}"
print(st_str)
log.append(st_str)


# NOTE: Don't give me shit about the cyclomatic complexity.
#       Nobody pays me to worry about it.

# try:
while True:
    prompt = input(Fore.BLUE + "--> " + Style.RESET_ALL)
    if prompt.lower() in ["b", "beacon"]:
        msgtype = "Beacon"
        last_beacon = time.time()
    elif prompt.lower() in ["s", "short"]:
        msgtype = "Short Beacon"
        last_beacon = time.time()
    elif prompt.lower() in ["l", "long"]:
        msgtype = "Long Beacon"
        last_beacon = time.time()
    elif prompt.lower() in ["a", "afsk"]:
        msgtype = "AFSK"
        last_afsk = time.time()
    elif prompt.lower() in ["c", "comment", "n", "note"]:
        log.append("# NOTE: " + get_comment())
        continue
    elif prompt.lower() in ["p", "ping"]:
        msgtype = "Ping"
    elif prompt.lower() in ["t", "time"]:
        print(
            f"""{current_time()} ({log_time(init_time)})
            Next AFSK in {next_msg(last_afsk, afsk_period)}
            Next beacon in {next_msg(last_beacon, beacon_period)}"""
        )
        continue
    elif prompt.lower() in ["d", "drill"]:
        msgtype = "Drill"
    elif prompt.lower() in ["h", "help"]:
        print(help_msg)
        continue
    elif prompt in ["q", "quit", "exit"]:
        rot.terminate()
        rig.terminate()
        break
    elif prompt in ["q!", "j", "jump"]:
        rot.terminate()
        rig.terminate()
        exit()
    else:
        continue

    az, el = rot.get_position().split()
    freq = rig.get_freq()
    curTime = current_time()
    logTime = log_time(init_time)

    if msgtype == "Beacon":
        msgtype = input("Short/Long Beacon: ") + " Beacon"
    if msgtype == "Ping":
        msgtype = (
            "Ping -> Pong" if input("Response? (y/N): ") == "y" else "Ping -> ____"
        )

    entry = f"""{curTime} ({logTime}) |\
f: {freq} | AZ: {az} | El: {el} |\
{msgtype}"""

    print(entry)

    if msgtype == "Drill":
        continue

    log.append(entry)

# Save the log file
log.append("\n")
file_name = time.strftime("%Y%m%d_%H%M%S.log", time.localtime(init_time))
with open(file_name, "w") as file:
    file.write("\n".join(log))

print(f"Saved to file {Fore.GREEN}'{file_name}'{Style.RESET_ALL}")

# except Exception:
#   rot.terminate()
#   rig.terminate()
