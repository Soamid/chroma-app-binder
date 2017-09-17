import subprocess
import time

import psutil
from rx import Observable
from rx.concurrency import NewThreadScheduler

CHROMA_APP_PATH = r'C:\ChromaApps\KeyboardVisualizer\KeyboardVisualizerVC_3.04.exe'

known_processes = set()

app_proc = None

def scan_processes(rx_subscriber):
    while True:
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                if p.name() == "Spotify.exe":
                    rx_subscriber.on_next(pid)
            except psutil.NoSuchProcess:
                pass
        time.sleep(1)


def wait_for_end(pid):
    def process_watcher():
        while check_if_running(pid):
            time.sleep(1)
        return pid

    return process_watcher


def check_if_running(pid):
    try:
        psutil.Process(pid)
    except psutil.NoSuchProcess:
        return False
    else:
        return True

def handle_audio_start(pid):
    global app_proc
    known_processes.add(pid)
    if not app_proc:
        SW_MINIMIZE = 6
        info = subprocess.STARTUPINFO()
        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = SW_MINIMIZE

        app_proc = subprocess.Popen(CHROMA_APP_PATH, startupinfo=info)
    print("START", pid, app_proc.pid)



def handle_audio_end(pid):
    print("KONIEC", pid, len(known_processes))
    known_processes.remove(pid)
    if not known_processes:
        try:
            global app_proc
            app_proc.kill()
            app_proc = None
        except SystemError:
            print('Error during killing chroma app')




scanner = Observable.create(lambda subscriber: scan_processes(subscriber)) \
    .subscribe_on(NewThreadScheduler()) \
    .publish()
scanner.distinct() \
    .subscribe(handle_audio_start)

scanner.distinct() \
    .flat_map(lambda pid: Observable.from_callable(wait_for_end(pid), NewThreadScheduler())) \
    .subscribe(handle_audio_end)
scanner.connect()

input()
