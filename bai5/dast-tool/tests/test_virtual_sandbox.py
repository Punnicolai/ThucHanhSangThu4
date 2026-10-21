import unittest

from virtual_sandbox import VirtualSandbox


class TestVirtualSandbox(unittest.TestCase):
    def test_runs_echo_in_temporary_directory(self):
        with VirtualSandbox() as sandbox:
            stdout, stderr = sandbox.run_isolated("echo test")
        self.assertEqual(stdout, "test\n")
        self.assertEqual(stderr, "")

    def test_rejects_other_commands(self):
        with VirtualSandbox() as sandbox:
            with self.assertRaises(ValueError):
                sandbox.run_isolated("python -c print(1)")


if __name__ == "__main__":
    unittest.main()
