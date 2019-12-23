#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Thomas Reifenberger.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import pmt
from gnuradio import gr, gr_unittest
from gnuradio import blocks
from binary_tagger import binary_tagger
from qa_common import ExpectedTag

TEST_KEY = 'test_key'


class qa_binary_tagger(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_zeroes_only_yield_no_tags(self):
        # given
        data = (0, 0, 0, 0, 0)
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), data)
        self._assert_tags(())

    def test_yields_starting_tag(self):
        # given
        data = (0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1)
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), data)
        self._assert_tags((
            ExpectedTag(2, TEST_KEY, True),
        ))

    def test_yields_starting_and_ending_tag(self):
        # given
        data = (0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0)
        self._setup_graph(data, max_quiet_samples=4)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), data)
        self._assert_tags((
            ExpectedTag(2, TEST_KEY, True),
            ExpectedTag(14, TEST_KEY, False),
        ))

    def test_yields_multiple_transmissions(self):
        # given
        data = (0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
        self._setup_graph(data, max_quiet_samples=2)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), data)
        self._assert_tags((
            ExpectedTag(2, TEST_KEY, True),
            ExpectedTag(7, TEST_KEY, False),
            ExpectedTag(9, TEST_KEY, True),
            ExpectedTag(15, TEST_KEY, False),
            ExpectedTag(16, TEST_KEY, True),
            ExpectedTag(19, TEST_KEY, False),
        ))

    def test_yields_transmissions_for_large_number_of_samples(self):
        # given
        data = (0,) * 100_000 + (1, 0, 0, 1, 0, 0, 1, 1) + (0,) * 100_000
        self._setup_graph(data, max_quiet_samples=10)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), data)
        self._assert_tags((
            ExpectedTag(100_000, TEST_KEY, True),
            ExpectedTag(100_018, TEST_KEY, False),
        ))

    def test_yields_transmissions_for_large_number_of_samples_with_long_transmission(self):
        # given
        data = (0,) * 100_000 + (1, 0, 0, 1, 0, 0, 1, 1) * 100_00 + (0,) * 11
        self._setup_graph(data, max_quiet_samples=10)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), data)
        self._assert_tags((
            ExpectedTag(100_000, TEST_KEY, True),
            ExpectedTag(180_010, TEST_KEY, False),
        ))

    def _setup_graph(self, src_data, max_quiet_samples=100):
        src = blocks.vector_source_b(src_data)
        uut = binary_tagger(key=TEST_KEY, max_quiet_samples=max_quiet_samples)
        self.dst = blocks.vector_sink_b()
        self.tb.connect(src, uut)
        self.tb.connect(uut, self.dst)

    def _assert_tags(self, tags: [ExpectedTag]):
        self.assertEqual(len(self.dst.tags()), len(tags))
        for tag, expected_tag in zip(self.dst.tags(), tags):
            self.assertEqual(tag.offset, expected_tag.offset)
            self.assertEqual(pmt.symbol_to_string(tag.key), expected_tag.key)
            self.assertEqual(pmt.to_python(tag.value), expected_tag.value)


if __name__ == '__main__':
    gr_unittest.run(qa_binary_tagger)
