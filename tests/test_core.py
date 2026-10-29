import datetime
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from protocol_versioner.cli import main
from protocol_versioner.core import ProtocolStore

V1 = "# DNA extraction\n\n1. Lyse cells 10 min\n2. Spin 5 min\n"
V2 = "# DNA extraction\n\n1. Lyse cells 15 min\n2. Spin 5 min\n3. Elute in 50 uL\n"


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.st = ProtocolStore(self.tmp.name, now=datetime.datetime(2026, 3, 1, 9, 0))

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_update_history(self):
        self.assertEqual(self.st.add("DNA Extraction", V1, "ana"), 1)
        self.assertEqual(self.st.update("dna extraction", V2, "bo", "longer lysis; added elution"), 2)
        h = self.st.history("DNA Extraction")
        self.assertEqual([v["note"] for v in h], ["initial version", "longer lysis; added elution"])
        self.assertEqual(self.st.protocols()[0]["title"], "DNA extraction")

    def test_rules(self):
        self.st.add("p", V1)
        with self.assertRaises(ValueError):
            self.st.add("p", V1)
        with self.assertRaises(ValueError):
            self.st.update("p", V2, note="")
        with self.assertRaises(ValueError):
            self.st.update("p", V1, note="no change")
        with self.assertRaises(KeyError):
            self.st.get("p", 9)

    def test_diff_and_export(self):
        self.st.add("p", V1, "ana")
        self.st.update("p", V2, "ana", "v2")
        d = self.st.diff("p", 1, 2)
        self.assertIn("-1. Lyse cells 10 min", d)
        self.assertIn("+3. Elute in 50 uL", d)
        exp = self.st.export("p", 1)
        self.assertTrue(exp.startswith("> **DNA extraction** | version 1 | 2026-03-01 | author: ana"))

    def test_tamper_detection_and_retire(self):
        self.st.add("p", V1)
        with open(os.path.join(self.tmp.name, "p", "v001.md"), "w", encoding="utf-8") as fh:
            fh.write("edited behind our back")
        with self.assertRaises(ValueError):
            self.st.get("p")
        self.st.retire("p", "replaced by kit")
        self.assertEqual(self.st.protocols()[0]["status"], "retired")

    def test_cli(self):
        src = os.path.join(self.tmp.name, "proto.md")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(V1)
        root = os.path.join(self.tmp.name, "store")
        with redirect_stdout(io.StringIO()) as buf, redirect_stderr(io.StringIO()):
            main(["--root", root, "add", "pcr", src])
            self.assertEqual(main(["--root", root, "update", "pcr", src, "-m", "same"]), 1)
            main(["--root", root, "list"])
        self.assertIn("pcr v1", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
