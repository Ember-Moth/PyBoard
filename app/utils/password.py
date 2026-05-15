"""密码哈希工具 —— 默认 Argon2id(PHC)，Bcrypt(MCF) 认证后自动升级。


格式检测：
    $argon2id$... → Argon2id（PHC）
    $2a$/$2b$...  → Bcrypt（MCF）
"""

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

_argon2 = PasswordHasher()


def hash_password(secret: str) -> str:
    """哈希密码，使用 Argon2id（PHC 格式）。

    Returns:
        $argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>
    """
    return _argon2.hash(secret)


def verify_and_upgrade(secret: str, hash: str) -> tuple[bool, str | None]:
    """验证密码，如果是 Bcrypt 则自动升级为 Argon2id。

    Args:
        secret: 用户输入的明文密码
        hash: 数据库中存储的哈希（Bcrypt 或 Argon2id）

    Returns:
        (True, None):       密码正确，已是 Argon2id，无需升级
        (True, new_hash):   密码正确，Bcrypt → Argon2id 升级完成
        (False, None):      密码错误
    """
    if hash.startswith("$argon2"):
        return _verify_argon2id(secret, hash)
    if hash.startswith("$2"):
        return _verify_bcrypt(secret, hash)
    return False, None


def _verify_argon2id(secret: str, hash: str) -> tuple[bool, str | None]:
    """Argon2id 验证，不升级。"""
    try:
        _argon2.verify(hash, secret)
        # 检查是否需要 rehash（参数变化时）
        if _argon2.check_needs_rehash(hash):
            return True, _argon2.hash(secret)
        return True, None
    except VerifyMismatchError:
        return False, None
    except VerificationError:
        return False, None


def _verify_bcrypt(secret: str, hash: str) -> tuple[bool, str | None]:
    """Bcrypt 验证，成功后升级为 Argon2id。"""
    try:
        if bcrypt.checkpw(secret.encode(), hash.encode()):
            return True, _argon2.hash(secret)  # 升级
        return False, None
    except (ValueError, TypeError):
        return False, None
