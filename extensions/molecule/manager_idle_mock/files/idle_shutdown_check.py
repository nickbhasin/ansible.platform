#!/usr/bin/env python3
"""Molecule helper: spawn manager with short idle_timeout and assert subprocess exits."""

from __future__ import absolute_import, division, print_function

import os
import sys
import time
from pathlib import Path

# Fast poll for CI (production default is 60s)
os.environ.setdefault("ANSIBLE_PLATFORM_MANAGER_IDLE_POLL_SECONDS", "1")

from ansible_collections.ansible.platform.plugins.plugin_utils.platform.config import GatewayConfig
import ansible_collections.ansible.platform.plugins.plugin_utils.manager.manager_process as mp
from ansible_collections.ansible.platform.plugins.plugin_utils.manager.process_manager import ProcessManager
from ansible_collections.ansible.platform.plugins.plugin_utils.manager.rpc_client import ManagerRPCClient


def main():
    gw = os.environ.get("GATEWAY_HOSTNAME", "http://127.0.0.1:8000")
    config = GatewayConfig(
        base_url=gw,
        username="mock",
        password="testpass",
        verify_ssl=False,
        request_timeout=30.0,
        connection_mode="experimental",
        idle_timeout=5.0,
    )
    socket_dir = Path("/tmp") / "ansible_platform"
    socket_dir.mkdir(exist_ok=True)
    conn = ProcessManager.generate_connection_info(
        identifier="molecule_idle_test",
        socket_dir=socket_dir,
        gateway_config=config,
    )
    ProcessManager.cleanup_old_socket(conn.socket_path)
    script_path = Path(mp.__file__).resolve()
    proc = ProcessManager.spawn_manager_process(
        script_path=script_path,
        socket_path=conn.socket_path,
        socket_dir=str(socket_dir),
        identifier="molecule_idle_test",
        gateway_config=config,
        authkey_b64=conn.authkey_b64,
        sys_path=list(sys.path),
    )
    ProcessManager.wait_for_process_startup(
        conn.socket_path,
        socket_dir,
        "molecule_idle_test",
        proc,
        max_wait=50,
    )
    client = ManagerRPCClient(config.base_url, conn.socket_path, conn.authkey)
    try:
        client.execute("find", "organization", {"name": "Default", "state": "present"})
    finally:
        client.close()

    # Poll interval 1s + idle_timeout 5s => allow margin
    deadline = time.time() + 30.0
    while time.time() < deadline:
        if not Path(conn.socket_path).exists():
            print("OK: socket removed")
            return 0
        if ProcessManager.is_socket_stale(conn.socket_path):
            print("OK: socket stale (process exited)")
            return 0
        time.sleep(0.3)

    print("FAIL: manager still running after idle timeout", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
