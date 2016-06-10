# -*- coding: utf-8; mode: python -*-

import Ice

INVALID_ADDRESS = "The value '{}' is not a valid IDM address"


def stringToAddress(str_identity):
    assert isinstance(str_identity, str)
    str_identity = str_identity.replace(':', '')

    try:
        retval = bytearray.fromhex(str_identity)
    except ValueError:
        raise ValueError(INVALID_ADDRESS.format(str_identity))

    if len(retval) < 2:
        retval = b'\x00' + retval

    return retval


def stringToIdentity(str_identity):
    str_identity = str_identity.replace(':', '')
    assert_hex(str_identity)
    if len(str_identity) < 4:
        raise ValueError(INVALID_ADDRESS.format(str_identity))

    return Ice.stringToIdentity(str_identity.upper())


def addressToString(address):
    assert isinstance(address, bytes)
    if len(address) < 2:
        raise ValueError(INVALID_ADDRESS.format(address))

    # Only Python3 solution:
    # return address.hex().upper()

    return "".join("{:02x}".format(ord(c)) for c in address).upper()


def assert_hex(text):
    int(text, 16)
