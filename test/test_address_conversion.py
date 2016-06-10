# -*- coding: utf-8; mode: python -*-

from unittest import TestCase
from libidm import stringToAddress, addressToString, stringToIdentity
import Ice


class TestStringToAddr(TestCase):
    def test_1234_to_addr(self):
        addr = stringToAddress('1234')
        self.assertEqual(b'\x12\x34', addr)
        self.assertEqual(0x12, addr[0])
        self.assertEqual(0x34, addr[1])

    def test_abc4_to_addr(self):
        self.assertEqual(b'\xab\xc4', stringToAddress('abc4'))

    def test_ABC4_to_addr(self):
        self.assertEqual(b'\xab\xc4', stringToAddress('abc4'))

    def test_12_34_to_addr(self):
        self.assertEqual(b'\x12\x34', stringToAddress('12:34'))

    def test_Z234_to_addr_is_error(self):
        with self.assertRaises(ValueError):
            stringToAddress('Z234')

    def test_0012_to_addr(self):
        self.assertEqual(b'\x00\x12', stringToAddress('0012'))

    def test_12_to_addr(self):
        self.assertEqual(b'\x00\x12', stringToAddress('12'))

    def test_123456_to_addr(self):
        self.assertEqual(b'\x12\x34\x56', stringToAddress('123456'))


class TestStringToIdentity(TestCase):
    def test_1234_to_IceIdentity(self):
        self.assertEqual(Ice.stringToIdentity('1234'),
                         stringToIdentity('1234'))

    def test_abc4_to_IceIdentity(self):
        self.assertEqual(Ice.stringToIdentity('ABC4'),
                         stringToIdentity('ab:c4'))

    def test_ABC4_to_IceIdentity(self):
        self.assertEqual(Ice.stringToIdentity('ABC4'),
                         stringToIdentity('AB:C4'))

    def test_12_34_to_IceIdentity(self):
        self.assertEqual(Ice.stringToIdentity('1234'),
                         stringToIdentity('12:34'))

    def test_Z234_to_IceIdentity_is_error(self):
        with self.assertRaises(ValueError):
            stringToIdentity('Z234')

    def test_0012_to_IceIdentity(self):
        self.assertEqual(Ice.stringToIdentity('0012'),
                         stringToIdentity('00:12'))

    def test_12_to_IceIdentity_is_error(self):
        with self.assertRaises(ValueError):
            stringToIdentity('12')

    def test_123456_to_IceIdentity(self):
        self.assertEqual(Ice.stringToIdentity('123456'),
                         stringToIdentity('12:34:56'))


class TestAddressToString(TestCase):
    def test_1234_to_str(self):
        self.assertEqual('1234', addressToString(b'\x12\x34'))

    def test_abc4_to_str(self):
        self.assertEqual('ABC4', addressToString(b'\xab\xc4'))

    def test_ABC4_to_str(self):
        self.assertEqual('ABC4', addressToString(b'\xAB\xC4'))

    def test_0012_to_str(self):
        self.assertEqual('0012', addressToString(b'\x00\x12'))

    def test_12_to_str_is_error(self):
        with self.assertRaises(ValueError):
            addressToString(b'\x12')

    def test_123456_to_str(self):
        self.assertEqual('123456', addressToString(b'\x12\x34\x56'))
