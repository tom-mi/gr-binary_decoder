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

import enum
import textwrap
import types

import pmt
from gnuradio import gr


class MessageType(enum.Enum):
    RAW = 'raw'
    PYTHON = 'python'
    PDU = 'pdu'


class binary_message_processor(gr.basic_block):
    """
    docstring for block binary_message_processor
    """

    def __init__(self, in_type=MessageType.PDU, out_type=MessageType.PDU, code='pass'):
        gr.basic_block.__init__(self,
                                name="binary_message_processor",
                                in_sig=None,
                                out_sig=None)

        if in_type == MessageType.RAW:
            self._decoder = self._raw_decoder
        elif in_type == MessageType.PYTHON:
            self._decoder = self._python_decoder
        elif in_type == MessageType.PDU:
            self._decoder = self._pdu_decoder
        else:
            raise ValueError(f'Unknown in_type {in_type}')

        if out_type == MessageType.RAW:
            self._encoder = self._raw_encoder
        elif out_type == MessageType.PYTHON:
            self._encoder = self._python_encoder
        elif out_type == MessageType.PDU:
            self._encoder = self._pdu_encoder
        else:
            raise ValueError(f'Unknown out_type {out_type}')
        new_locals = {}
        if in_type == MessageType.PDU:
            header = 'def process(tags, data):\n'
        else:
            header = 'def process(message):\n'
        exec(header + textwrap.indent(code, prefix='    '), globals(), new_locals)

        self._processor = new_locals['process']

        self.message_port_register_in(pmt.intern('in'))
        self.message_port_register_out(pmt.intern('out'))
        self.set_msg_handler(pmt.intern('in'), self._handle_message)

    def _handle_message(self, message):
        args = self._decoder(message)
        result = self._processor(*args)
        if result is not None:
            if isinstance(result, types.GeneratorType):
                for result_item in result:
                    encoded_result = self._encoder(result_item)
                    self.message_port_pub(pmt.intern('out'), encoded_result)
            else:
                encoded_result = self._encoder(result)
                self.message_port_pub(pmt.intern('out'), encoded_result)

    @staticmethod
    def _raw_decoder(message):
        return message,

    @staticmethod
    def _python_decoder(message):
        return pmt.to_python(message),

    @staticmethod
    def _pdu_decoder(message):
        tags = pmt.to_python(pmt.car(message))
        data = pmt.to_python(pmt.cdr(message))
        return tags, data

    @staticmethod
    def _raw_encoder(message):
        return message

    @staticmethod
    def _python_encoder(message):
        return pmt.to_pmt(message)

    @staticmethod
    def _pdu_encoder(result):
        (tags, data) = result
        return pmt.cons(pmt.to_pmt(tags), pmt.to_pmt(data))
