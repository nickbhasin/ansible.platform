"""Integration check: manager subprocess exits after idle_timeout (ansible-test target)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Shorter poll in CI; production default is 60s
os.environ.setdefault("ANSIBLE_PLATFORM_MANAGER_IDLE_POLL_SECONDS", "2")

from ansible_collections.ansible.platform.plugins.plugin_utils.platform.config import GatewayConfig
from ansible_collections.ansible.platform.plugins.plugin_utils.manager import manager_process as mp
from ansible_collections.ansible.platform.plugins.plugin_utils.manager.process_manager import ProcessManager
from ansible_collections.ansible.platform.plugins.plugin_utils.manager.rpc_client import ManagerRPCClient


def main() -> int:
    gw = os.environ["GATEWAY_HOSTNAME"]
    user = os.environ["GATEWAY_USERNAME"]
    password = os.environ["GATEWAY_PASSWORD"]
    verify = os.environ.get("GATEWAY_VALIDATE_CERTS", "true").lower() in ("1", "true", "yes")
    test_id = os.environ.get("IDLE_TEST_ID", "integration")
    idle = float(os.environ.get("MANAGER_IDLE_TIMEOUT_SEC", "8"))

    config = GatewayConfig(
        base_url=gw,
        username=user,
        password=password,
        verify_ssl=verify,
        request_timeout=float(os.environ.get("GATEWAY_REQUEST_TIMEOUT", "60")),
        connection_mode="experimental",
        idle_timeout=idle,
    )

    identifier = f"idle_integ_{test_id}"
    socket_dir = Path("/tmp") / "ansible_platform"
    socket_dir.mkdir(exist_ok=True)
    conn = ProcessManager.generate_connection_info(
        identifier=identifier,
        socket_dir=socket_dir,
        gateway_config=config,
    )
    ProcessManager.cleanup_old_socket(conn.socket_path)
    script_path = Path(mp.__file__).resolve()
    proc = ProcessManager.spawn_manager_process(
        script_path=script_path,
        socket_path=conn.socket_path,
        socket_dir=str(socket_dir),
        identifier=identifier,
        gateway_config=config,
        authkey_b64=conn.authkey_b64,
        sys_path=list(sys.path),
    )
    ProcessManager.wait_for_process_startup(
        conn.socket_path,
        socket_dir,
        identifier,
        proc,
        max_wait=50,
    )
    client = ManagerRPCClient(config.base_url, conn.socket_path, conn.authkey)
    try:
        client.execute("find", "organization", {"name": "Default", "state": "present"})
    finally:
        client.close()

    deadline = time.time() + 45.0
    while time.time() < deadline:
        if not Path(conn.socket_path).exists():
            print("OK: socket removed after idle timeout", file=sys.stderr)
            return 0
        if ProcessManager.is_socket_stale(conn.socket_path):
            print("OK: manager process exited (stale socket)", file=sys.stderr)
            return 0
        time.sleep(0.25)

    print("FAIL: manager still up after idle period", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
