# Connection modes and manager process

The Ansible Platform collection can talk to the Automation Platform gateway in **direct** mode (short-lived HTTP clients) or **persistent** mode (a dedicated **manager subprocess** that holds a session and serves RPC over a Unix socket). See also `docs/03-sdk-architecture.md` for lifecycle diagrams.

## Persistent manager (`ansible.platform.http` + persistent)

When `persistent` is enabled (connection option or `ansible_platform_use_persistent_connection` / `ansible_platform_persistent`), the collection spawns one manager process per matching `(host, gateway URL, credentials)` tuple and reuses it across tasks.

### Manager idle timeout (`idle_timeout`)

The manager subprocess is designed to exit when it has been **idle** (no RPC activity such as `execute` or `lookup_resource_id`) for longer than **`idle_timeout`** seconds, so abandoned processes do not linger after playbooks or when cleanup is missed.

| Setting | Description |
|--------|-------------|
| **Default** | `3600` (one hour), in seconds |
| **Disable** | Set to `0` — no idle watchdog (manager only stops on graceful shutdown, e.g. end of play cleanup or signal) |
| **Variables** | `platform_manager_idle_timeout` (task/host/inventory) or `ansible_platform_manager_idle_timeout` (host/inventory) |
| **Model field** | `GatewayConfig.idle_timeout` (used by the manager subprocess and tests) |

Idle detection uses a background thread in the manager process that wakes **every 60 seconds** (see below) and compares elapsed idle time to `idle_timeout`. When the threshold is exceeded, the manager calls `shutdown()`, stops the IPC server, and the subprocess exits; the socket and PID file are removed on exit.

### Poll interval (operational default)

The idle check runs **every 60 seconds**. For automated tests only, the interval can be overridden with:

`ANSIBLE_PLATFORM_MANAGER_IDLE_POLL_SECONDS`

Production playbooks should rely on the default 60-second polling behavior.

## Direct / ephemeral manager

When `persistent` is false, an **ephemeral** manager may still be spawned per task (depending on connection and client path) and is torn down after the task; **`idle_timeout` still applies** to that subprocess if it remains running without RPC traffic (for example if the Ansible process disconnects without calling shutdown).

## Related configuration

- **HTTP request timeout**: `gateway_request_timeout` — per HTTP call, unrelated to manager idle shutdown.
- **AAP route/service `idle_timeout_seconds`**: API fields on gateway routes and services; not the same as **manager** `idle_timeout`.
