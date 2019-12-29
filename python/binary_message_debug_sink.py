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

import numpy
import pmt
from gnuradio import gr


class binary_message_debug_sink(gr.basic_block):
    """
    docstring for block binary_message_debug_sink
    """

    def __init__(self, output='pmt', binary_output='hex', bytes_per_sep=1):
        gr.basic_block.__init__(self,
                                name="binary_message_debug_sink",
                                in_sig=None,
                                out_sig=None)
        self.message_port_register_in(pmt.intern('in'))
        self.message_port_register_in(pmt.intern('pdu_in'))

        if output in ['raw', 'python']:
            self._printer = self._get_printer(output, bytes_per_sep)
        else:
            raise ValueError(f'Unknown output type {output}')
        if binary_output in ['raw', 'python', 'hex']:
            self._binary_printer = self._get_printer(binary_output, bytes_per_sep)
        else:
            raise ValueError(f'Unknown binary_output type {binary_output}')

        self.set_msg_handler(pmt.intern('in'), self._handle_message)
        self.set_msg_handler(pmt.intern('pdu_in'), self._handle_pdu_message)

    def _get_printer(self, type_, bytes_per_sep):
        if type_ == 'raw':
            return self._print_message_raw
        elif type_ == 'python':
            return self._print_message_python
        elif type_ == 'hex':
            return self._print_message_hex(bytes_per_sep)
        else:
            raise ValueError(f'Unknown output type {type_}')

    def _handle_message(self, message):
        if self._is_binary(message):
            self._binary_printer(message)
        else:
            self._printer(message)

    def _handle_pdu_message(self, message):
        if not pmt.is_pair(message):
            print('Invalid pdu: ', message)
        else:
            data = pmt.cdr(message)
            if self._is_binary(data):
                self._binary_printer(data)
            else:
                self._printer(data)

    @staticmethod
    def _is_binary(message):
        return pmt.is_u8vector(message)

    @staticmethod
    def _extract_binary_pdu_data(self, message):
        return pmt.to_python(pmt.cdr(message))

    @staticmethod
    def _print_message_raw(message):
        print(message)

    @staticmethod
    def _print_message_python(message):
        print(pmt.to_python(message))

    @staticmethod
    def _print_message_hex(bytes_per_sep):
        def handler(message):
            decoded_message = pmt.to_python(message)
            if type(decoded_message) != numpy.ndarray or decoded_message.dtype != numpy.uint8:
                raise ValueError('Binary printer can only print arrays of uint8')
            print(bytes.hex(decoded_message.tobytes(), ' ', bytes_per_sep=bytes_per_sep))

        return handler
