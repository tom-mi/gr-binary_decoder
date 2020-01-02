#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 Thomas Reifenberger.
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

import time

import numpy
import pmt
from gnuradio import gr_unittest
from binary_message_processor import binary_message_processor, MessageType
from qa_common import message_source, BinaryBaseTest, message_sink

VECTOR = numpy.array([0, 1, 2], dtype='uint8')


class qa_binary_message_processor(BinaryBaseTest):

    def test_no_messages_yield_no_result(self):
        # given
        self._setup_graph([])

        # when
        self._run()

        # then
        self.assertEqual(self.dst.messages, [])

    def test_encoding_decoding(self):
        for in_type, out_type, in_data, out_data, code in [(
                MessageType.RAW, MessageType.RAW,
                pmt.to_pmt('foo'), pmt.to_pmt('foo'),
                'return message',
        ), (
                MessageType.RAW, MessageType.PYTHON,
                pmt.to_pmt('foo'), pmt.to_pmt('foo'),
                'return pmt.to_python(message)',
        ), (
                MessageType.RAW, MessageType.PDU,
                pmt.to_pmt(VECTOR), pmt.cons(pmt.to_pmt({'foo': 'bar'}), pmt.to_pmt(VECTOR)),
                'return {"foo": "bar"}, pmt.to_python(message)',
        ), (
                MessageType.PYTHON, MessageType.PYTHON,
                pmt.to_pmt('foo'), pmt.to_pmt('foo'),
                'return message',
        ), (
                MessageType.PYTHON, MessageType.RAW,
                pmt.to_pmt('foo'), pmt.to_pmt('foo'),
                'return pmt.to_pmt(message)',
        ), (
                MessageType.PYTHON, MessageType.PDU,
                pmt.to_pmt(VECTOR), pmt.cons(pmt.to_pmt({'foo': 'bar'}), pmt.to_pmt(VECTOR)),
                'return {"foo": "bar"}, message',
        ), (
                MessageType.PDU, MessageType.RAW,
                pmt.cons(pmt.PMT_NIL, pmt.to_pmt(VECTOR)), pmt.to_pmt(VECTOR),
                'return pmt.to_pmt(data)',
        ), (
                MessageType.PDU, MessageType.PYTHON,
                pmt.cons(pmt.PMT_NIL, pmt.to_pmt(VECTOR)), pmt.to_pmt(VECTOR),
                'return data',
        ), (
                MessageType.PDU, MessageType.PDU,
                pmt.cons(pmt.to_pmt({'foo': 'bar'}), pmt.to_pmt(numpy.array([0, 1, 2], dtype='uint8'))),
                pmt.cons(pmt.to_pmt({'foo': 'bar'}), pmt.to_pmt(numpy.array([0, 1, 2], dtype='uint8'))),
                'return tags, data',
        )]:
            with self.subTest(in_type=in_type, out_type=out_type):
                # sub-tests don't call tearDown / setUp
                self.tearDown()
                self.setUp()
                # given
                self._setup_graph([in_data], in_type=in_type, out_type=out_type, code=code)

                # when
                self._run()

                # then
                self.assertMessages([out_data])

    def test_does_nothing_if_None_is_returned(self):
        for in_type, out_type, in_data in [(
                MessageType.RAW, MessageType.RAW, pmt.to_pmt('foo')
        ), (
                MessageType.RAW, MessageType.PYTHON, pmt.to_pmt('foo')
        ), (
                MessageType.RAW, MessageType.PDU, pmt.to_pmt(VECTOR)
        )]:
            with self.subTest(in_type=in_type, out_type=out_type):
                # sub-tests don't call tearDown / setUp
                self.tearDown()
                self.setUp()
                # given
                self._setup_graph([in_data], in_type=in_type, out_type=out_type, code='pass')

                # when
                self._run()

                # then
                self.assertMessages([])

    def test_returns_multiple_messages(self):
        # given
        code = 'yield "foo"\nyield "bar"'
        self._setup_graph([pmt.PMT_NIL], in_type=MessageType.RAW, out_type=MessageType.PYTHON, code=code)

        # when
        self._run()

        # then
        self.assertMessages([pmt.to_pmt('foo'), pmt.to_pmt('bar')])

    def test_advanced_processing(self):
        code = 'return len(message)'
        self._setup_graph([pmt.to_pmt('foobar')], in_type=MessageType.PYTHON, out_type=MessageType.PYTHON, code=code)

        # when
        self._run()

        # then
        self.assertMessages([pmt.to_pmt(6)])

    def test_advanced_processing_with_multiple_messages(self):
        code = 'yield from message.split()'
        self._setup_graph([pmt.to_pmt('foo bar')], in_type=MessageType.PYTHON, out_type=MessageType.PYTHON, code=code)

        # when
        self._run()

        # then
        self.assertMessages([pmt.to_pmt('foo'), pmt.to_pmt('bar')])

    def assertMessages(self, expected_messages):
        expected_pythonic_messages = [pmt.to_python(message) for message in expected_messages]
        actual_pythonic_messages = [pmt.to_python(message) for message in self.dst.messages]
        numpy.testing.assert_equal(actual_pythonic_messages, expected_pythonic_messages)

    def _run(self):
        self.tb.start()
        time.sleep(0.001)
        self.tb.stop()
        self.tb.wait()

    def _setup_graph(self, src_messages, in_type=MessageType.RAW, out_type=MessageType.RAW, code='pass'):
        src = message_source(src_messages)
        uut = binary_message_processor(in_type=in_type, out_type=out_type, code=code)
        self.dst = message_sink()
        self.tb.msg_connect(src, 'out', uut, 'in')
        self.tb.msg_connect(uut, 'out', self.dst, 'in')


if __name__ == '__main__':
    gr_unittest.run(qa_binary_message_processor)
