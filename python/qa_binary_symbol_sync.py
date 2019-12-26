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

from gnuradio import gr_unittest

from binary_symbol_sync import binary_symbol_sync
from qa_common import BinaryBaseTest


class qa_binary_symbol_sync(BinaryBaseTest):

    def test_zeroes_only_yield_no_output(self):
        # given
        data = (0,) * 20
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), ())

    def test_returns_single_symbol(self):
        # given
        data = (1, 1, 0, 0, 0) + (0,)
        self._setup_graph(data, samples_per_symbol=5, max_deviation=0)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,))

    def test_returns_multiple_symbols(self):
        # given
        data = (1, 1, 0, 0, 0) * 2 + (0, 0, 0, 0, 0) * 2 + (1, 0, 1, 0, 0) + (0,)
        self._setup_graph(data, samples_per_symbol=5, max_deviation=0)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 1, 0, 0, 1))

    def test_returns_multiple_symbols_with_leading_zeros(self):
        # given
        data = (0,) * 13 + (1, 1, 0, 0, 0) * 2 + (0, 0, 0, 0, 0) * 2 + (1, 0, 1, 0, 0) + (0,)
        self._setup_graph(data, samples_per_symbol=5, max_deviation=0)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 1, 0, 0, 1))

    def test_returns_multiple_symbols_with_trailing_zeros_but_loses_lock_after_more_than_max_zero_symbols(self):
        # given
        data = (1, 1, 0, 0, 0) * 2 + (0, 0, 0, 0, 0) * 2 + (1, 0, 1, 0, 0) + (0,) * 5 * 4
        self._setup_graph(data, samples_per_symbol=5, max_deviation=0, max_zero_symbols=2)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 1, 0, 0, 1, 0, 0, 0))

    def test_interpolates_output_samples(self):
        # given
        data = (1, 1, 0, 0, 0) + (0, 0, 0, 0, 0) + (1, 0, 1, 0, 0) + (0,)
        self._setup_graph(data, samples_per_symbol=5, max_deviation=0, max_zero_symbols=2, output_samples_per_symbol=3)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 1, 0) + (0, 0, 0) + (1, 0, 0))

    def test_handles_unstable_clock(self):
        # given
        data = (1, 1, 0, 0, 0) + (0, 0, 0, 0, 0) + (1, 0, 1, 0, 0, 0, 0) + (1, 1, 0) + (1, 1, 0, 1, 0) + (0,) * 30
        self._setup_graph(data, samples_per_symbol=5, max_deviation=2, max_zero_symbols=2, output_samples_per_symbol=2)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 0) + (0, 0) + (1, 0) + (1, 1) + (1, 0) + (0, 0) * 3)

    def test_handles_lock_to_drifted_clock(self):
        # given
        data = (1, 1, 0, 0, 0, 0, 0, 0) * 4 + (0, 0, 0, 0, 0, 0, 0, 0) * 4 + (1, 1, 0, 0, 0, 0, 0, 0) * 2 + (0,) * 10
        self._setup_graph(data, samples_per_symbol=10, max_deviation=3, max_zero_symbols=4, output_samples_per_symbol=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 1, 1, 1, 0, 0, 0, 0, 1, 1))

    def test_handles_lock_to_drifted_clock_with_custom_smoothing_factor(self):
        # given
        data = (1, 1, 0, 0, 0, 0, 0, 0) * 2 + (0, 0, 0, 0, 0, 0, 0, 0) * 4 + (1, 1, 0, 0, 0, 0, 0, 0) * 2 + (0,) * 10
        self._setup_graph(data, samples_per_symbol=10, max_deviation=3, clock_smoothing_factor=0.9, max_zero_symbols=4)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 1, 0, 0, 0, 0, 1, 1))

    def test_handles_multiple_transmissions(self):
        # given
        one = (1, 1, 0, 0, 0)
        zero = (0, 0, 0, 0, 0)
        data = one * 3 + zero + one + zero * 5 + one * 3 + one + one + zero * 4
        self._setup_graph(data, samples_per_symbol=5, max_deviation=1, max_zero_symbols=2, output_samples_per_symbol=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0))

    def test_handles_large_amounts_of_zeros(self):
        # given
        one = (1, 1, 0, 0, 0)
        zero = (0, 0, 0, 0, 0)
        data = zero * 100_000 + one * 10 + zero * 100_000 + one * 10 + zero * 100_000
        self._setup_graph(data, samples_per_symbol=5, max_deviation=1, max_zero_symbols=2, output_samples_per_symbol=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,) * 10 + (0,) * 3 + (1,) * 10 + (0,) * 3)

    def test_handles_large_amounts_of_data(self):
        # given
        one = (1, 1, 0, 0, 0)
        zero = (0, 0, 0, 0, 0)
        data = zero * 100_000 + one * 100_000 + zero * 100_000 + one * 100_000 + zero * 100_000
        self._setup_graph(data, samples_per_symbol=5, max_deviation=1, max_zero_symbols=2, output_samples_per_symbol=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,) * 100_000 + (0,) * 3 + (1,) * 100_000 + (0,) * 3)

    def _setup_graph(self, src_data, samples_per_symbol=10, clock_smoothing_factor=0.5,
                     max_deviation=2, max_zero_symbols=5, output_samples_per_symbol=1):
        uut = binary_symbol_sync(
            samples_per_symbol=samples_per_symbol,
            max_deviation=max_deviation,
            clock_smoothing_factor=clock_smoothing_factor,
            max_zero_symbols=max_zero_symbols,
            output_samples_per_symbol=output_samples_per_symbol,
        )
        self._setup_graph_with_uut(src_data, uut)


if __name__ == '__main__':
    gr_unittest.run(qa_binary_symbol_sync)
