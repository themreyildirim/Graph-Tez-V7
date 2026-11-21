"""Post-lock audit: notebook now includes its sixth, executed closing QA cell.

The earlier 36-test log belongs to the five-cell, pre-finalisation notebook.
Keep that log/test fixture immutable; adapt only the final notebook expectation here.
"""
import test_wp13_external_reference_v1 as before
from pathlib import Path
import hashlib

r=before.r

class ClosureTests(before.ReferenceTests):
    def test_32_executed_notebook_no_errors(self):
        n=r.read(r.ROOT/'notebooks/WP13_EXTERNAL_REFERENCE_COMPARISON_v1.ipynb')
        cells=[c for c in n['cells'] if c['cell_type']=='code']
        self.assertEqual([c['execution_count'] for c in cells],list(range(1,7)))
        self.assertTrue(all(c['outputs'] for c in cells))
        self.assertFalse(any(o['output_type']=='error' for c in cells for o in c['outputs']))
    def test_37_complete_delivered_evidence_manifest(self):
        pins=r.read(r.Q/'evidence_manifest.json');self.assertEqual(len(pins),70);r.verify_pins(pins)
    def test_38_reference_lock_independent_digest(self):
        expected='89cc467d8677605e0a0b136ad10be3e72be98d392a284c583bcc83361c726b5a'
        self.assertEqual(hashlib.sha256((r.Q/'reference_comparison_lock.json').read_bytes()).hexdigest(),expected)
        r.verify_pins(r.read(r.Q/'reference_comparison_lock.json')['outputs_sha256'])

if __name__=='__main__':before.unittest.main(verbosity=2)
