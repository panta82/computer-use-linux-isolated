#!/usr/bin/python3
"""Service-bus routing must not leak into the isolated application environment."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

source = Path(__file__).resolve().parents[1] / 'desktop/manage.py'
function = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'systemctl')

class ServiceBusTests(unittest.TestCase):
    def setUp(self):
        self.uid = os.getuid()
        self.run = Mock(return_value=SimpleNamespace(returncode=0))
        self.namespace = {'os': os, 'pathlib': SimpleNamespace(Path=Path), 'subprocess': SimpleNamespace(run=self.run)}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), self.namespace)

    def invoke(self, env):
        with patch.dict(os.environ, env, clear=True), patch.object(Path, 'is_dir', return_value=True), patch.object(Path, 'stat', return_value=SimpleNamespace(st_uid=self.uid)), patch.object(Path, 'is_socket', return_value=True):
            before = dict(os.environ)
            self.namespace['systemctl']('start', 'computer-use-linux-isolated.service', check=True)
            self.assertEqual(dict(os.environ), before)
        args, kwargs = self.run.call_args
        self.assertEqual(args[0], ['systemctl', '--user', 'start', 'computer-use-linux-isolated.service'])
        self.assertEqual(kwargs['env']['XDG_RUNTIME_DIR'], f'/run/user/{self.uid}')
        self.assertEqual(kwargs['env']['DBUS_SESSION_BUS_ADDRESS'], f'unix:path=/run/user/{self.uid}/bus')
        self.assertTrue(kwargs['check'])

    def test_missing_session_environment(self):
        self.invoke({'PATH': '/usr/bin:/bin'})

    def test_private_bus_is_not_used_for_service_management(self):
        self.invoke({'DISPLAY': ':199', 'XDG_RUNTIME_DIR': '/private/session', 'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/private/session/bus'})
        self.assertEqual(self.run.call_args.kwargs['env']['DISPLAY'], ':199')

    def test_missing_user_bus_fails_without_calling_systemctl(self):
        with patch.object(Path, 'is_dir', return_value=True), patch.object(Path, 'stat', return_value=SimpleNamespace(st_uid=self.uid)), patch.object(Path, 'is_socket', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'User service manager unavailable'):
                self.namespace['systemctl']('start', 'computer-use-linux-isolated.service')
        self.run.assert_not_called()

    def test_foreign_owned_runtime_is_rejected(self):
        with patch.object(Path, 'is_dir', return_value=True), patch.object(Path, 'stat', return_value=SimpleNamespace(st_uid=self.uid + 1)):
            with self.assertRaisesRegex(RuntimeError, 'User service manager unavailable'):
                self.namespace['systemctl']('start', 'computer-use-linux-isolated.service')
        self.run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
