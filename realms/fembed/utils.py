import base64
from Crypto.Cipher import AES


def safe_b64decode(s):
    s = s.strip().replace("\n", "").replace("\r", "")
    s = s.replace("-", "+").replace("_", "/")
    missing_padding = len(s) % 4
    if missing_padding:
        s += "=" * (4 - missing_padding)

    return base64.b64decode(s)


def try_decrypt(payload_bytes, iv_bytes, key_bytes):
    try:
        tag = payload_bytes[-16:]
        ciphertext = payload_bytes[:-16]

        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=iv_bytes)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
        return True, decrypted_data.decode("utf-8")
    except Exception as e:
        return False, str(e)


def decrypt_AEG(payload: str, iv: str, key_parts: list[str], legacy: str) -> None | str:
    if len(key_parts) != 2:
        return None
    payload = safe_b64decode(payload)
    iv = safe_b64decode(iv)
    p0 = safe_b64decode(key_parts[0])
    p1 = safe_b64decode(key_parts[1])

    possibilities = [
        ("Concatenação p0+p1", p0 + p1),
        ("Legacy String Bytes", legacy.encode("utf-8")),
        ("Legacy Base64 Decode", safe_b64decode(legacy)),
    ]
    for nome, chave in possibilities:
        if len(chave) != 32:
            continue

        success, result = try_decrypt(payload, iv, chave)
        if success:
            print(result)
            return result
    return None
