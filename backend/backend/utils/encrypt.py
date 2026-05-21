"""Encrypt."""

import os
import hashlib
from typing import Any

from itsdangerous import URLSafeSerializer
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends.openssl import backend
from cryptography.hazmat.primitives.ciphers import Cipher, modes, algorithms

from backend.common.log import log


def normalize_key(key: bytes | bytearray | memoryview | str) -> bytes:
    """Normalize Key."""
    if isinstance(key, str):
        return bytes.fromhex(key)
    return bytes(key)


class AESCipher:
    """AES 加密器."""

    def __init__(self, key: bytes | bytearray | memoryview | str) -> None:
        """初始化 AES 加密器.

        :param key: 密钥，16/24/32 bytes 或 16 进制字符串
        :return:
        """
        self.key = normalize_key(key)

    def encrypt(self, plaintext: bytes | str) -> bytes:
        """AES 加密.

        :param plaintext: 加密前的明文
        :return:
        """
        if not isinstance(plaintext, bytes):
            plaintext = str(plaintext).encode("utf-8")
        iv = os.urandom(16)
        aes = algorithms.AES(self.key)
        cipher = Cipher(aes, modes.CBC(iv), backend=backend)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(aes.block_size).padder()
        padded_plaintext = padder.update(plaintext) + padder.finalize()
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        return iv + ciphertext

    def decrypt(self, ciphertext: bytes | bytearray | memoryview | str) -> str:
        """AES 解密.

        :param ciphertext: 解密前的密文，bytes 或 16 进制字符串
        :return:
        """
        ciphertext_bytes = bytes.fromhex(ciphertext) if isinstance(ciphertext, str) else bytes(ciphertext)
        iv = ciphertext_bytes[:16]
        ciphertext_bytes = ciphertext_bytes[16:]
        aes = algorithms.AES(self.key)
        cipher = Cipher(aes, modes.CBC(iv), backend=backend)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(aes.block_size).unpadder()
        padded_plaintext = decryptor.update(ciphertext_bytes) + decryptor.finalize()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        return plaintext.decode("utf-8")


class Md5Cipher:
    """MD5 加密器."""

    @staticmethod
    def encrypt(plaintext: bytes | str) -> str:
        """MD5 加密.

        :param plaintext: 加密前的明文
        :return:
        """
        md5 = hashlib.md5()  # noqa: S324
        if not isinstance(plaintext, bytes):
            plaintext = str(plaintext).encode("utf-8")
        md5.update(plaintext)
        return md5.hexdigest()


class ItsDCipher:
    """ItsDangerous 加密器."""

    def __init__(self, key: bytes | bytearray | memoryview | str) -> None:
        """初始化 ItsDangerous 加密器.

        :param key: 密钥，16/24/32 bytes 或 16 进制字符串
        :return:
        """
        self.key = normalize_key(key)

    def encrypt(self, plaintext: Any) -> str:  # noqa: ANN401
        """ItsDangerous 加密.

        :param plaintext: 加密前的明文
        :return:
        """
        serializer = URLSafeSerializer(self.key)
        try:
            ciphertext = serializer.dumps(plaintext)
        except Exception as e:
            log.error(f"ItsDangerous encrypt failed: {e}")
            ciphertext = Md5Cipher.encrypt(plaintext)
        return ciphertext

    def decrypt(self, ciphertext: str) -> Any:  # noqa: ANN401
        """ItsDangerous 解密.

        :param ciphertext: 解密前的密文
        :return:
        """
        serializer = URLSafeSerializer(self.key)
        try:
            plaintext = serializer.loads(ciphertext)
        except Exception as e:
            log.error(f"ItsDangerous decrypt failed: {e}")
            plaintext = ciphertext
        return plaintext
