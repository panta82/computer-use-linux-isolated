#!/usr/bin/env python3
"""Check startup ownership rules without launching or changing a desktop."""
import ast
import os
from pathlib import Path
import stat
import tempfile
import unittest

source = Path(__file__).resolve().parents[1] / 'desktop/session.py'
functions = [node for node in ast.parse(source.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in ('private_directory', 'verify_display_owner')]
namespace = {'os': os, 'pathlib': __import__('pathlib'), 'stat': stat}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), namespace)


class StartupTests(unittest.TestCase):
    def test_private_directory_rejects_symlink_and_shared_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / 'target'
            target.mkdir(mode=0o755)
            link = root / 'link'
            link.symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, 'Unsafe'):
                namespace['private_directory'](link)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o755)
            target.chmod(0o777)
            with self.assertRaisesRegex(RuntimeError, 'Unsafe'):
                namespace['private_directory'](target)
            target.chmod(0o700)
            namespace['private_directory'](target)

    def test_display_must_belong_to_the_started_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / 'X199-lock'
            for content in ('', 'broken', '999'):
                lock.write_text(content)
                with self.assertRaises(RuntimeError):
                    namespace['verify_display_owner'](123, lock)
            lock.write_text('       123\n')
            namespace['verify_display_owner'](123, lock)
            lock.unlink()
            with self.assertRaisesRegex(RuntimeError, 'Cannot verify'):
                namespace['verify_display_owner'](123, lock)


if __name__ == '__main__':
    unittest.main()
