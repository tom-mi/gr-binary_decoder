from dataclasses import dataclass

import pmt
from gnuradio import gr, gr_unittest, blocks

TEST_KEY = 'test_key'


@dataclass
class ExpectedTag(object):
    offset: int
    key: str
    value: object


class BinaryBaseTest(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def _setup_graph_with_uut(self, src_data, uut):
        src = blocks.vector_source_b(src_data)
        self.dst = blocks.vector_sink_b()
        self.tb.connect(src, uut)
        self.tb.connect(uut, self.dst)

    def _assert_tags(self, tags: [ExpectedTag]):
        self.assertEqual(len(self.dst.tags()), len(tags))
        for tag, expected_tag in zip(self.dst.tags(), tags):
            self.assertEqual(tag.offset, expected_tag.offset)
            self.assertEqual(pmt.symbol_to_string(tag.key), expected_tag.key)
            self.assertEqual(pmt.to_python(tag.value), expected_tag.value)
