"""x509 stub."""
def load_pem_x509_certificate(data):
    class _Cert:
        def public_key(self):
            return None
    return _Cert()
