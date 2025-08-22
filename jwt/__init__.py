"""Minimal jwt stub for tests."""
class PyJWTError(Exception):
    pass

def encode(*args, **kwargs):
    return ''

def decode(*args, **kwargs):
    return {}

def get_unverified_header(*args, **kwargs):
    return {}

class algorithms:
    class RSAAlgorithm:
        @staticmethod
        def from_jwk(data):
            return None
