import os
import random
import time
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import Flask, request, jsonify
from consistent_hash import ConsistentHashMap

app = Flask(__name__)
ring = ConsistentHashMap(num_slots=512, k_virtual=9)
lock = threading.Lock()

SERVER_IMAGE = "server-image:latest"
NETWORK_NAME = "net1"

# Persistent connection pool to handle 10,000+ fast requests without socket exhaustion
session = requests.Session()
adapter = HTTPAdapter(pool_connections=200, pool_maxsize=200, max_retries=Retry(total=2, backoff_factor=0.1))
session.mount('http://', adapter)

def run_cmd(cmd: str) -> str:
    stream = os.popen(cmd)
    return stream.read().strip()

def spawn_server(hostname: str):
    server_id = ''.join([c for c in hostname if c.isdigit()]) or hostname
    cmd = (
        f"docker run -d --name {hostname} --network {NETWORK_NAME} "
        f"--network-alias {hostname} -e SERVER_ID={server_id} {SERVER_IMAGE}"
    )
    run_cmd(cmd)

def kill_server(hostname: str):
    run_cmd(f"docker stop {hostname} && docker rm {hostname}")

def heartbeat_monitor():
    while True:
        time.sleep(0.5)
        with lock:
            servers = ring.get_all_servers()

        for hostname in servers:
            failed = False
            try:
                res = requests.get(f"http://{hostname}:5000/heartbeat", timeout=0.8)
                if res.status_code != 200:
                    failed = True
            except Exception:
                failed = True

            if failed:
                with lock:
                    if hostname in ring.get_all_servers():
                        print(f"[Heartbeat] Failure detected on {hostname}. Recovering...")
                        ring.remove_server(hostname)
                        kill_server(hostname)
                        
                        new_host = f"Server_{random.randint(1000, 9999)}"
                        spawn_server(new_host)
                        ring.add_server(new_host)
                        print(f"[Heartbeat] Spawned {new_host} as replacement.")

@app.route('/rep', methods=['GET'])
def get_replicas():
    with lock:
        servers = ring.get_all_servers()
        return jsonify({
            "message": {
                "N": len(servers),
                "replicas": servers
            },
            "status": "successful"
        }), 200

@app.route('/add', methods=['POST'])
def add_replicas():
    data = request.get_json() or {}
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    new_servers = []
    for name in hostnames:
        new_servers.append(name)

    for _ in range(n - len(hostnames)):
        new_servers.append(f"Server_{random.randint(1000, 9999)}")

    with lock:
        for host in new_servers:
            spawn_server(host)
            ring.add_server(host)
        servers = ring.get_all_servers()

    return jsonify({
        "message": {
            "N": len(servers),
            "replicas": servers
        },
        "status": "successful"
    }), 200

@app.route('/rm', methods=['DELETE', 'POST'])
def remove_replicas():
    data = request.get_json() or {}
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    with lock:
        current_servers = ring.get_all_servers()
        if n > len(current_servers):
            return jsonify({
                "message": "<Error> Cannot remove more instances than currently active",
                "status": "failure"
            }), 400

        to_remove = list(hostnames)
        remaining = [s for s in current_servers if s not in to_remove]

        while len(to_remove) < n and remaining:
            chosen = random.choice(remaining)
            to_remove.append(chosen)
            remaining.remove(chosen)

        for host in to_remove:
            ring.remove_server(host)
            kill_server(host)

        servers = ring.get_all_servers()

    return jsonify({
        "message": {
            "N": len(servers),
            "replicas": servers
        },
        "status": "successful"
    }), 200

@app.route('/<path:path>', methods=['GET'])
def route_request(path):
    req_id = random.randint(100000, 999999)
    with lock:
        target_server = ring.get_server(req_id)

    if not target_server:
        return jsonify({"message": "<Error> No active server replicas", "status": "failure"}), 500

    try:
        url = f"http://{target_server}:5000/{path}"
        res = session.get(url, timeout=2)
        return jsonify(res.json()), res.status_code
    except Exception:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
            "status": "failure"
        }), 400

if __name__ == '__main__':
    default_servers = ["Server_1", "Server_2", "Server_3"]
    for host in default_servers:
        spawn_server(host)
        ring.add_server(host)

    t = threading.Thread(target=heartbeat_monitor, daemon=True)
    t.start()

    app.run(host='0.0.0.0', port=5000, threaded=True)