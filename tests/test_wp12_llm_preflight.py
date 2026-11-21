"""Ön kontrol bellek kapısı; LLM veya Ollama çağırmaz."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wp12_local_llm_preflight import memory_gate


class MemoryGateTests(unittest.TestCase):
    def test_low_host_memory_blocks_even_free_GPU(self):
        self.assertFalse(memory_gate(1*2**30,3935))

    def test_low_GPU_blocks_even_free_RAM(self):
        self.assertFalse(memory_gate(4*2**30,1024))

    def test_floor_pass_is_not_fit_guarantee(self):
        self.assertTrue(memory_gate(3*2**30,2560))

    def test_just_below_RAM_floor_blocks(self):
        self.assertFalse(memory_gate(3*2**30-1,2560))

    def test_nonfinite_or_missing_measurement_blocks(self):
        for a,b in [(None,3935),(float('nan'),3935),(4*2**30,float('inf'))]:
            self.assertFalse(memory_gate(a,b))

    def test_negative_and_boolean_measurement_blocks(self):
        self.assertFalse(memory_gate(-1,3935))
        self.assertFalse(memory_gate(True,3935))


if __name__=='__main__':
    unittest.main(verbosity=2)
