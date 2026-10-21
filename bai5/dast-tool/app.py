import os
from pathlib import Path

from flask import Flask, jsonify, request

from memory_analyzer import MemoryAnalyzer
from network_traffic_analyzer import NetworkTrafficAnalyzer
from runtime_monitor import RuntimeMonitor
from security_behavior_checker import SecurityBehaviorChecker
from virtual_sandbox import VirtualSandbox

app = Flask(__name__)


@app.get("/api/monitor")
def monitor():
    runtime = RuntimeMonitor(os.getpid())
    return jsonify(
        {
            "cpu_usage": runtime.get_cpu_usage(),
            "memory_usage": runtime.get_memory_usage(),
            "open_files": [file.path for file in runtime.get_open_files()],
        }
    )


@app.get("/api/memory")
def memory():
    analyzer = MemoryAnalyzer()
    return jsonify(
        {
            "memory_leak_count": len(analyzer.check_memory_leaks()),
            "overflow_test": analyzer.check_overflow(2**64),
        }
    )


@app.get("/api/network")
def network():
    stats = NetworkTrafficAnalyzer().get_network_stats()
    return jsonify({"network_stats": stats})


@app.get("/api/security")
def security():
    checker = SecurityBehaviorChecker(Path(__file__))
    suspicious_calls = checker.suspicious_calls()
    return jsonify({"suspicious_calls": suspicious_calls})


@app.post("/api/sandbox")
def sandbox():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "command" not in data:
        return jsonify({"error": "JSON body must contain a command."}), 400
    try:
        with VirtualSandbox() as virtual_sandbox:
            stdout, stderr = virtual_sandbox.run_isolated(data["command"])
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"stdout": stdout, "stderr": stderr})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
