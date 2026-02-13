"""Tests for the custom serve management command."""

from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase


class ServeCommandTests(TestCase):
    """Tests for the serve management command."""

    @patch("project.management.commands.serve.WSGIServer")
    @patch("project.management.commands.serve.get_wsgi_application")
    def test_starts_server_without_tls(self, mock_get_app, mock_server):
        """Command initializes server with host, port, and numthreads."""
        mock_get_app.return_value = object()
        server_instance = mock_server.return_value
        call_command("serve", host="127.0.0.1", port=9000, numthreads=5)
        mock_server.assert_called_once()
        args, kwargs = mock_server.call_args
        self.assertEqual(args[0], ("127.0.0.1", 9000))
        self.assertIn("numthreads", kwargs)
        self.assertEqual(kwargs["numthreads"], 5)
        server_instance.start.assert_called_once()

    @patch("project.management.commands.serve.WSGIServer")
    @patch("project.management.commands.serve.get_wsgi_application")
    def test_starts_server_with_tls(self, mock_get_app, mock_server):
        """Command passes TLS options when cert and key are provided."""
        mock_get_app.return_value = object()
        server_instance = mock_server.return_value
        call_command(
            "serve",
            host="0.0.0.0",
            port=9443,
            numthreads=2,
            tls_cert="/tmp/cert.pem",
            tls_key="/tmp/key.pem",
        )
        args, kwargs = mock_server.call_args
        self.assertEqual(args[0], ("0.0.0.0", 9443))
        self.assertEqual(kwargs.get("ssl_certificate"), "/tmp/cert.pem")
        self.assertEqual(kwargs.get("ssl_private_key"), "/tmp/key.pem")
        server_instance.start.assert_called_once()
