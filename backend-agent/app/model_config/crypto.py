"""模型 API Key 的静态加密。

为什么不用 `cryptography`：本机离线环境没有该依赖，而模型配置是管理端低频写、
Agent 高频读的场景，先把「密钥不落明文」做出来比引入一个装不上的包更实际。

实现是标准的 Encrypt-then-MAC：
- 加密：HMAC-SHA256 作为 PRF 的计数器模式（CTR）生成密钥流，与明文异或；
- 认证：HMAC-SHA256 覆盖版本号 + nonce + 密文，解密前用 `compare_digest` 校验；
- 主密钥：优先 `PET_AGENT_CONFIG_SECRET`；未配置时在 `data/` 下生成 32 字节随机文件
  （0600），避免把密钥写进仓库或数据库。

生产环境建议把主密钥托管到 KMS/Vault，并替换为经过审计的 AEAD 实现；
这里的格式带版本前缀，后续可以在不破坏旧数据的前提下升级。
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import os
import secrets
from pathlib import Path

_VERSION = b"v1"
_NONCE_BYTES = 16
_TAG_BYTES = 32
_KEY_BYTES = 32


class ConfigCipherError(ValueError):
    """密钥材料损坏、密文被篡改或格式不合法。"""


class ConfigCipher:
    def __init__(self, secret: str, key_file: str | Path) -> None:
        master = self._master_key(secret, Path(key_file))
        # 加密与认证使用不同的子密钥，避免同一密钥跨用途
        self._enc_key = hmac.new(master, b"petlumina/model-config/enc", hashlib.sha256).digest()
        self._mac_key = hmac.new(master, b"petlumina/model-config/mac", hashlib.sha256).digest()

    @staticmethod
    def _master_key(secret: str, key_file: Path) -> bytes:
        if secret:
            return hashlib.sha256(("petlumina/model-config:" + secret).encode("utf-8")).digest()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        if key_file.exists():
            data = key_file.read_bytes()
            if len(data) != _KEY_BYTES:
                raise ConfigCipherError(f"密钥文件长度异常：{key_file}")
            return data
        data = secrets.token_bytes(_KEY_BYTES)
        try:
            with key_file.open("xb") as fh:
                fh.write(data)
            with contextlib.suppress(OSError):
                os.chmod(key_file, 0o600)
        except FileExistsError:
            # 并发首次启动：另一个进程已经写入，读它的即可
            data = key_file.read_bytes()
            if len(data) != _KEY_BYTES:
                raise ConfigCipherError(f"密钥文件长度异常：{key_file}") from None
        return data

    def encrypt(self, plaintext: str) -> str:
        raw = plaintext.encode("utf-8")
        nonce = secrets.token_bytes(_NONCE_BYTES)
        ciphertext = _xor(raw, self._keystream(nonce, len(raw)))
        tag = hmac.new(self._mac_key, _VERSION + nonce + ciphertext, hashlib.sha256).digest()
        return "v1:" + base64.urlsafe_b64encode(nonce + tag + ciphertext).decode("ascii")

    def decrypt(self, token: str) -> str:
        if not token.startswith("v1:"):
            raise ConfigCipherError("不支持的密钥密文版本")
        try:
            payload = base64.urlsafe_b64decode(token[3:].encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise ConfigCipherError("密钥密文不是合法 base64") from exc
        if len(payload) < _NONCE_BYTES + _TAG_BYTES:
            raise ConfigCipherError("密钥密文长度不足")
        nonce = payload[:_NONCE_BYTES]
        tag = payload[_NONCE_BYTES : _NONCE_BYTES + _TAG_BYTES]
        ciphertext = payload[_NONCE_BYTES + _TAG_BYTES :]
        expected = hmac.new(self._mac_key, _VERSION + nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise ConfigCipherError("密钥密文校验失败")
        return _xor(ciphertext, self._keystream(nonce, len(ciphertext))).decode("utf-8")

    def _keystream(self, nonce: bytes, length: int) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < length:
            out.extend(hmac.new(self._enc_key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest())
            counter += 1
        return bytes(out[:length])


def _xor(data: bytes, stream: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, stream, strict=True))
