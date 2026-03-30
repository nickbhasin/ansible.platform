# (c) 2026 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for PlatformService manager idle shutdown."""

from __future__ import absolute_import, division, print_function

import unittest
from unittest.mock import MagicMock, patch

from ansible_collections.ansible.platform.plugins.plugin_utils.platform.config import GatewayConfig
from ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager import PlatformService


class TestPlatformServiceIdle(unittest.TestCase):
    @patch("ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager.get_credential_manager")
    @patch("ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager._get_requests")
    def test_idle_timeout_zero_skips_monitor_thread(self, mock_get_requests, mock_cred_manager):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {
            "current_version": "/api/gateway/v1/",
            "available_versions": {"v1": "/api/gateway/v1/"},
        }
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_requests = MagicMock()
        mock_requests.Session.return_value = mock_session
        mock_get_requests.return_value = mock_requests
        mock_store = MagicMock()
        mock_store.get_auth_credentials.return_value = ("admin", "admin", None)
        mock_cred_manager.return_value.get_or_create_store.return_value = mock_store

        config = GatewayConfig(
            base_url="https://127.0.0.1",
            username="admin",
            password="admin",
            idle_timeout=0.0,
        )
        service = PlatformService(config)
        service.attach_manager_server(MagicMock())
        self.assertIsNone(service._idle_monitor_thread)

    @patch("ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager.get_credential_manager")
    @patch("ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager._get_requests")
    def test_idle_monitor_starts_when_timeout_positive(self, mock_get_requests, mock_cred_manager):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {
            "current_version": "/api/gateway/v1/",
            "available_versions": {"v1": "/api/gateway/v1/"},
        }
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_requests = MagicMock()
        mock_requests.Session.return_value = mock_session
        mock_get_requests.return_value = mock_requests
        mock_store = MagicMock()
        mock_store.get_auth_credentials.return_value = ("admin", "admin", None)
        mock_cred_manager.return_value.get_or_create_store.return_value = mock_store

        config = GatewayConfig(
            base_url="https://127.0.0.1",
            username="admin",
            password="admin",
            idle_timeout=30.0,
        )
        service = PlatformService(config)
        service.attach_manager_server(MagicMock())
        self.assertIsNotNone(service._idle_monitor_thread)
        self.assertTrue(service._idle_monitor_thread.is_alive())

    @patch("ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager.get_credential_manager")
    @patch("ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager._get_requests")
    @patch("ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager.time.sleep")
    @patch("ansible_collections.ansible.platform.plugins.plugin_utils.manager.platform_manager.time.monotonic")
    def test_idle_monitor_calls_server_shutdown_after_timeout(
        self, mock_monotonic, mock_sleep, mock_get_requests, mock_cred_manager
    ):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {
            "current_version": "/api/gateway/v1/",
            "available_versions": {"v1": "/api/gateway/v1/"},
        }
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_requests = MagicMock()
        mock_requests.Session.return_value = mock_session
        mock_get_requests.return_value = mock_requests
        mock_store = MagicMock()
        mock_store.get_auth_credentials.return_value = ("admin", "admin", None)
        mock_cred_manager.return_value.get_or_create_store.return_value = mock_store

        mock_server = MagicMock()
        config = GatewayConfig(
            base_url="https://127.0.0.1",
            username="admin",
            password="admin",
            idle_timeout=10.0,
        )
        service = PlatformService(config)
        service._last_activity_monotonic = 0.0
        mock_monotonic.return_value = 100.0
        mock_sleep.return_value = None

        service.attach_manager_server(mock_server)
        service._idle_monitor_thread.join(timeout=5.0)

        mock_server.shutdown.assert_called()


if __name__ == "__main__":
    unittest.main()
