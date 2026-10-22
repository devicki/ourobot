import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
import interview  # noqa: E402


class ParseTest(unittest.TestCase):
    def test_start(self):
        p = interview.parse("Interview started. Session ID: interview_20261022_132316\n\nHow?\n\n<!-- adv -->junk")
        self.assertEqual(p["session_id"], "interview_20261022_132316")
        self.assertEqual(p["question"], "How?")

    def test_answer_prefix(self):
        p = interview.parse("Session interview_20261022_132343\n\nWhat format?")
        self.assertEqual(p["question"], "What format?")
        self.assertFalse(p["completed"])


if __name__ == "__main__":
    unittest.main()
