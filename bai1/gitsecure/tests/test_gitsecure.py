import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('gitsecure',Path(__file__).parents[1]/'gitsecure.py')
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

class HookTests(unittest.TestCase):
    def test_sensitive_assignment(self): self.assertTrue(g.scan_sensitive('password = '+repr('demo'+'12345')))
    def test_safe_environment_reference(self): self.assertFalse(g.scan_sensitive('secret = os.environ["KEY"]'))
    def test_windows_permissions(self): self.assertFalse(g.check_permissions(0o100777,'nt'))
    def test_posix_world_writable(self): self.assertTrue(g.check_permissions(0o100777,'posix'))
    def test_posix_safe_permissions(self): self.assertFalse(g.check_permissions(0o100644,'posix'))
    def test_license_reject_unknown(self):
        policy={'approved_packages':{},'allowed_licenses':['MIT']}
        self.assertTrue(g.check_license('unknown-package==1.0',policy))
    def test_license_reject_unpinned(self):
        self.assertTrue(g.check_license('Flask',{'approved_packages':{'flask':'BSD-3-Clause'},'allowed_licenses':['BSD-3-Clause']}))

if __name__=='__main__': unittest.main(verbosity=2)
