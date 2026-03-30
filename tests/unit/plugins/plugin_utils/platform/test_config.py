# (c) 2026 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Tests for GatewayConfig and extract_gateway_config (idle timeout)."""

from __future__ import absolute_import, division, print_function

import unittest

from ansible_collections.ansible.platform.plugins.plugin_utils.platform.config import (
    GatewayConfig,
    extract_gateway_config,
)


class TestGatewayIdleTimeout(unittest.TestCase):
    def test_gateway_config_default_idle_timeout(self):
        c = GatewayConfig(base_url="https://example.com")
        self.assertEqual(c.idle_timeout, 3600.0)

    def test_extract_gateway_config_respects_task_arg(self):
        c = extract_gateway_config(
            task_args={
                "gateway_url": "https://gw.example",
                "platform_manager_idle_timeout": 120,
            },
            host_vars={},
            required=True,
        )
        self.assertEqual(c.idle_timeout, 120.0)

    def test_extract_gateway_config_host_var_alias(self):
        c = extract_gateway_config(
            task_args={"gateway_url": "https://gw.example"},
            host_vars={"ansible_platform_manager_idle_timeout": "90"},
            required=True,
        )
        self.assertEqual(c.idle_timeout, 90.0)

    def test_extract_gateway_config_zero_disables_in_config(self):
        c = extract_gateway_config(
            task_args={
                "gateway_url": "https://gw.example",
                "platform_manager_idle_timeout": 0,
            },
            host_vars={},
            required=True,
        )
        self.assertEqual(c.idle_timeout, 0.0)


if __name__ == "__main__":
    unittest.main()
