import logging
import os
import inspect
import subprocess
import time
from multiprocessing import Process
from threading import Thread

import psutil
from colorama import Fore, init
from icecream import ic
from kivy.utils import platform

from .utils import (
    ALWAYS_ON_TOP,
    PHONE_IPS,
    PORT,
    SHOW_TOUCHES,
    STAY_AWAKE,
    STREAM_USING,
    TURN_SCREEN_OFF,
    WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_X,
    WINDOW_Y,
)

if platform in ["linux", "macosx"]:
    from plyer import notification

yellow = Fore.YELLOW
init(autoreset=True)

ForceApplicationExit = (KeyboardInterrupt,
                        UnboundLocalError)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def notify(title: str, message: str) -> None:
    """
    Send a notification to the user's desktop.
    No support for Windows yet.
    """
    if platform in ["linux", "macosx"]:
        notification.notify(message=message, title=title)


def start_compilation(option: int, app_name: str) -> None:
    """
    Starts the compilation process based on the given option.
    """
    try:
        if option == "1":
            logging.info("Starting compilation")
            notify(
                f"Compiling {app_name}",
                f"Compilation started at {time.strftime('%H:%M:%S')}",
            )
            t1 = time.time()
            subprocess.run(
                ["buildozer", "-v", "android", "debug", "deploy", "run"], check=True
            )
            t2 = time.time()
            notify(
                f"Compiled {app_name} successfully",
                f"Compilation finished in {round(t2 - t1, 2)} seconds",
            )
            logging.info("Finished compilation")
            debug_and_livestream()
        else:
            debug_and_livestream()
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred during compilation: {e}")


def debug_and_livestream() -> None:
    """
    Executes `adb logcat` and `scrcpy` in parallel.
    """
    try:
        adb_logcat = Process(target=debug)
        scrcpy = Process(target=livestream)

        adb_logcat.start()
        scrcpy.start()
    except KeyboardInterrupt:
        logging.info("Terminating processes")
        adb_logcat.terminate()
        scrcpy.terminate()


def debug():
    """
    Debugging based on the streaming method.
    """
    try:
        if STREAM_USING == "USB":
            restart_adb_server()
            clear_logcat()
            run_logcat()
        elif STREAM_USING == "WIFI":
            debug_on_wifi()
    except ForceApplicationExit:
        logging.info("scrcpy closing by user.")


def restart_adb_server():
    """
    Restarts the adb server.
    """
    logging.info("Restarting adb server")
    subprocess.run(["adb", "disconnect"])
    subprocess.run(["adb", "kill-server"])
    subprocess.run(["adb", "start-server"])


def clear_logcat():
    """
    Clears the logcat.
    """
    logging.info("Clearing logcat")
    subprocess.run(["adb", "logcat", "-c"])


def ping(ip):
    try:
        resultado = subprocess.check_output(['ping', '-c', '1', ip])
        print(f'{ip} is active.')
        return True
    except subprocess.CalledProcessError:
        print(f'{ip} is not active.')


def debug_on_wifi():
    """
    Debugging over WiFi.
    """
    restart_adb_server()
    subprocess.run(["adb", "tcpip", f"{PORT}"])

    for IP in PHONE_IPS:
        # start each logcat on a thread
        if ping(IP):
            t = Thread(target=run_logcat, args=(IP,))
            t.start()


def run_logcat(IP=None, *args):
    """
    Runs logcat for debugging.
    """
    logcat_command = "adb logcat | grep 'I python'"

    if IP:
        subprocess.run(["adb", "connect", f"{IP}"])
        logcat_command.replace("adb", f"adb -s {IP}:{PORT}")

    logging.info("Starting logcat")
    subprocess.run(logcat_command, shell=True)


def livestream():
    """
    Handles the livestream process.
    """
    if STREAM_USING == "WIFI":
        time.sleep(3)

    for proc in psutil.process_iter():
        try:
            if proc.name() == "scrcpy":
                logging.info("scrcpy already running")
                return
        except psutil.NoSuchProcess:
            logging.error("Error while trying to find scrcpy process")
    try:
        start_scrcpy()
    except ForceApplicationExit:
        logging.info("scrcpy closing by user.")


def start_scrcpy():
    """
    Starts the scrcpy process for screen mirroring.
    """
    logging.info("Starting scrcpy")
    command = [
        "scrcpy",
        "--window-x",
        WINDOW_X,
        "--window-y",
        WINDOW_Y,
        "--window-width",
        WINDOW_WIDTH,
    ]

    if STREAM_USING == "USB":
        if ALWAYS_ON_TOP:
            command.append("--always-on-top")
        if TURN_SCREEN_OFF:
            command.append("--turn-screen-off")
        if STAY_AWAKE:
            command.append("--stay-awake")
        if SHOW_TOUCHES:
            command.append("--show-touches")
        if WINDOW_TITLE:
            command.append("--window-title")
            command.append(WINDOW_TITLE)
        command.append("-d")
    elif STREAM_USING == "WIFI":
        command.append("-e")

    subprocess.run(command)


def get_app_name():
    """
    Extracts the application name from the 'buildozer.spec' file.
    """
    with open("buildozer.spec", "r") as file:
        for line in file:
            if line.startswith("title"):
                return line.split("=")[1].strip()
    return "UnknownApp"


def start(main_file):
    """
    Entry point for the script. Prompts the user to choose an option.
    """
    print(f"{yellow} Choose an option:")
    app_name = get_app_name()
    try:
        option = input("1 - Compile, debug and livestream\n2 - Debug and livestream\n")
        start_compilation(option, app_name)
        path_of_current_file = inspect.currentframe().f_back
        path_of_send_app = os.path.join(
            os.path.dirname(
                os.path.abspath(path_of_current_file.f_code.co_filename)
            ),
            main_file,
        )
        subprocess.run(f"python {path_of_send_app} no-window", shell=True)
    except ForceApplicationExit:
        logging.info("Exiting application...")
        return


if __name__ == "__main__":
    start()
