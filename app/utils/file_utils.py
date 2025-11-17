import hashlib


def sha256sum(data: bytes) -> str:
    """Calcula el hash SHA256 de los datos"""
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

