"""Teknik metadata/bütçe testleri; model veya Ollama yüklenmez."""
import io
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_gemma_memory as m


class MemoryTests(unittest.TestCase):
    def test_real_metadata_only(self):
        x=m.read_metadata(m.MODEL_BLOB)
        self.assertEqual(x['metadata']['gemma3.block_count'],26)
        self.assertEqual(x['metadata']['gemma3.attention.head_count_kv'],1)
        self.assertLess(x['metadata_span_bytes'],7*2**20)
        self.assertFalse(x['tensor_data_read'])

    def test_KV_formula(self):
        x=m.read_metadata(m.MODEL_BLOB)
        self.assertEqual(m.kv_bytes(x,2048,2),52*2**20)
        self.assertEqual(m.kv_bytes(x,2048,4),104*2**20)

    def test_context_linear_upper_envelope(self):
        x=m.read_metadata(m.MODEL_BLOB)
        self.assertEqual(m.kv_bytes(x,1024,4)*2,m.kv_bytes(x,2048,4))

    def test_truncated_header_rejected(self):
        with patch.object(Path,'open',return_value=io.BytesIO(b'GGUF')):
            with self.assertRaises(ValueError):m.read_metadata('unused')

    def test_invalid_magic_rejected(self):
        with patch.object(Path,'open',return_value=io.BytesIO(b'BAD!')):
            with self.assertRaises(ValueError):m.read_metadata('unused')

    def test_budget_below_rounded_gates(self):
        b=m.budget(m.read_metadata(m.MODEL_BLOB))
        self.assertLess(b['host_budget_total_bytes'],b['host_admission_bytes'])
        self.assertLess(b['GPU_budget_total_bytes'],b['GPU_admission_MiB']*2**20)
        self.assertFalse(b['guaranteed_safe'])

    def test_v2_boundaries_and_commit(self):
        self.assertTrue(m.admission(2684354560,2048,3*2**30))
        for x in [(2684354559,2048,3*2**30),(2684354560,2047,3*2**30),(2684354560,2048,3*2**30-1)]:
            self.assertFalse(m.admission(*x))

    def test_unknown_or_nonfinite_fails_closed(self):
        self.assertFalse(m.admission(None,2048,4*2**30))
        self.assertFalse(m.admission(float('nan'),2048,4*2**30))


if __name__=='__main__':unittest.main(verbosity=2)
