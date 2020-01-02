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
import contextlib
import io
import time

import numpy
import pmt
from gnuradio import gr_unittest
from binary_message_debug_sink import binary_message_debug_sink, OutputType
from qa_common import message_source, BinaryBaseTest


class qa_binary_message_debug_sink(BinaryBaseTest):

    def test_no_messages_yield_no_result(self):
        # given
        self._setup_graph([])

        # when
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self._run()

        # then
        self.assertEqual(out.getvalue(), '')

    def test_generic_output(self):
        messages = [pmt.to_pmt('foo'), pmt.to_pmt('bar'), pmt.to_pmt({'foo': [1, 2]})]
        for parameters, expected_output in [
            (dict(output=OutputType.RAW), 'foo\nbar\n((foo . #(1 2)))\n'),
            (dict(output=OutputType.PYTHON), "foo\nbar\n{'foo': [1, 2]}\n"),

        ]:
            with self.subTest(parameters=parameters, expected_output=expected_output):
                # sub-tests don't call tearDown / setUp
                self.tearDown()
                self.setUp()
                # given
                self._setup_graph(messages, **parameters)

                # when
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self._run()

                # then
                self.assertEqual(out.getvalue(), expected_output)

    def test_raw_binary_output(self):
        # some non-printable bytes cause problems in the test setup when printed raw
        # given
        self._setup_graph([pmt.to_pmt(numpy.array([0x00, 0x01, 0x42, 0x70], dtype='uint8'))],
                          binary_output=OutputType.RAW)

        # when
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self._run()

        # then
        self.assertEqual(out.getvalue(), '#[\x00 \x01 \x42 \x70]\n')

    def test_binary_output(self):
        messages = [pmt.to_pmt(numpy.array([0, 1, 255, 4, 4, 5, 8, 9, 66, 42], dtype='uint8'))]
        for parameters, expected_output in [
            (dict(binary_output=OutputType.PYTHON), "[  0   1 255   4   4   5   8   9  66  42]\n"),
            (dict(binary_output=OutputType.HEX), '00 01 ff 04 04 05 08 09 42 2a\n'),
            (dict(binary_output=OutputType.HEX, bytes_per_sep=4), '0001 ff040405 0809422a\n'),
            (dict(binary_output=OutputType.HEX, bytes_per_sep=-4), '0001ff04 04050809 422a\n'),
        ]:
            with self.subTest(f'{parameters} -> {expected_output}'):
                # sub-tests don't call tearDown / setUp
                self.tearDown()
                self.setUp()
                # given
                self._setup_graph(messages, **parameters)

                # when
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self._run()

                # then
                self.assertEqual(out.getvalue(), expected_output)

    def test_binary_pdu(self):
        messages = [
            pmt.cons(pmt.PMT_NIL, pmt.to_pmt(numpy.array([0, 1, 255, 4, 4, 5, 8, 9, 66, 42], dtype='uint8'))),
        ]
        for parameters, expected_output in [
            (dict(binary_output=OutputType.PYTHON), "[  0   1 255   4   4   5   8   9  66  42]\n"),
            (dict(binary_output=OutputType.HEX), '00 01 ff 04 04 05 08 09 42 2a\n'),
            (dict(binary_output=OutputType.HEX, bytes_per_sep=4), '0001 ff040405 0809422a\n'),
            (dict(binary_output=OutputType.HEX, bytes_per_sep=-4), '0001ff04 04050809 422a\n'),
        ]:
            with self.subTest(f'{parameters} -> {expected_output}'):
                # sub-tests don't call tearDown / setUp
                self.tearDown()
                self.setUp()
                # given
                self._setup_graph(messages, pdu_in=True, **parameters)

                # when
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self._run()

                # then
                self.assertEqual(out.getvalue(), expected_output)

    def _run(self):
        self.tb.start()
        time.sleep(0.001)
        self.tb.stop()
        self.tb.wait()

    def _setup_graph(self, src_messages, pdu_in=False, output=OutputType.RAW, binary_output=OutputType.HEX,
                     bytes_per_sep=1):
        src = message_source(src_messages)
        uut = binary_message_debug_sink(output=output, binary_output=binary_output, bytes_per_sep=bytes_per_sep)
        self.tb.msg_connect(src, 'out', uut, 'pdu_in' if pdu_in else 'in')


if __name__ == '__main__':
    gr_unittest.run(qa_binary_message_debug_sink)
