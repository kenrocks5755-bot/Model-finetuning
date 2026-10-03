import json
import tempfile
import unittest
from pathlib import Path

from relearn.convert import convert_file
from relearn.io import read_records
from relearn.split import split_records
from relearn.validate import validate


class PipelineTest(unittest.TestCase):
    def test_conversion_scrubs_deduplicates_and_splits_groups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "pymeta.jsonl"
            rows = [
                {"problem": "Write a loop", "code": "print('x') # 10.2.3.4", "student_id": "alice", "task_id": "p1", "verdict": "wrong"},
                {"problem": "Write a loop", "code": "print('x') # 10.2.3.4", "student_id": "alice", "task_id": "p1", "verdict": "wrong"},
                {"problem": "Add numbers", "code": "print(1+1)", "student_id": "bob", "task_id": "p2", "error": "none"},
            ]
            source.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
            converted = root / "converted.jsonl"
            stats = convert_file(source, converted, "pymeta")
            self.assertEqual(stats["output"], 2)
            records, _ = split_records(list(read_records(converted)), seed=1)
            self.assertEqual(validate(records, require_all_splits=False)["ok"], True)
            self.assertNotIn("10.2.3.4", json.dumps(records))
            self.assertEqual(len({r["split"] for r in records if r["learner_id"] == records[0]["learner_id"]}), 1)


if __name__ == "__main__":
    unittest.main()
