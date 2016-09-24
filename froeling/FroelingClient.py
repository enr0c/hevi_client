#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from .SerialClient import SerialClient 
from .FroelingValueConverter import *

from datetime import datetime

class FroelingClient(object):

  def __init__(self, port):
    self.client = SerialClient(port)

  def test_connection(self):
    result = self.client.single_communication(b'\x22', fr_bytes("Hello froeling.io!"))
    return fr_string(result['body'])

  def load_recent_values(self, schema):
    values = {}
    for s in schema:
      if s['address'] != b'':
        verify_values = []
        for i in range(0, 3):
          result = self.client.single_communication(b'\x30', s['address'])
          if result is not None:
            verify_values.append(result['body'])
        if len(verify_values) > 0:
          value = max(set(verify_values), key=verify_values.count)
          values[fr_hex(s['address'])] = (fr_int(value) / s['factor'])
    return values

  def load_recent_values_schema(self):
    result = self.client.multiple_communication(b'\x31', b'01', b'\x32', b'01')
    parsed_values = []
    for unit in result:
      body = unit['body']
      if len(body) > 9:
        parsed_values.append({'factor': fr_int(body[1:3]), 'unit': chr(body[6]), 'address': body[7:9], 'description': fr_string(body[9:len(body)-1])})
    return parsed_values

  def load_menu_structure(self):
    result = self.client.multiple_communication(b'\x37', b'01', b'\x38', b'01')
    parsed_values = []
    for entry in result:
      body = entry['body']
      if len(body) > 30:
        parsed_values.append({
          'description': fr_string(body[29:len(body) - 1]), 
          'address': body[25:27],
          'type': body[1],
          'parent': body[3:5],
          'child': body[5:7]
        })
    return parsed_values

  def load_errors(self):
    result = self.client.multiple_communication(b'\x47', b'', b'\x48', b'')
    parsed_errors = []
    for error in result:
      body = error['body']
      if len(body) > 11:
        error_number = body[2]
        error_info = body[3] 
        error_state = body[4]
        
        error_time = str(body[7]) + ':' + str(body[6]) + ':' + str(body[5])
        error_date = str(body[8]) + '.' + str(body[9]) + '.' + str(body[10])
        timestamp = int(datetime.strptime(error_time + " " + error_date, '%H:%M:%S %d.%m.%y').timestamp())

        description = fr_string(body[11:])
        parsed_errors.append({
          'number': error_number, 'info': error_info, 'state': error_state, 'timestamp': timestamp, 'description': description
        })
    return parsed_errors

  def load_config(self):
    result = self.client.single_communication(b'\x40', b'')
    return result

  def load_version_date(self):
    result = self.client.single_communication(b'\x41', b'')
    body = result['body']

    date = str(body[7]) + '.' + str(body[8]) + '.' + str(body[10])
    time = str(body[6]) + ':' + str(body[5]) + ':' + str(body[4])
    timestamp = int(datetime.strptime(time + " " + date, '%H:%M:%S %d.%m.%y').timestamp())

    value = {'version': fr_hex(body[0:4]), 'timestamp': timestamp}
    return value

  def load_state(self):
    result = self.client.single_communication(b'\x51', b'')
    data = fr_string(result['body'][2:]).split(";")
    value = {'mode': data[0].strip(), 'state': data[1]}
    return value