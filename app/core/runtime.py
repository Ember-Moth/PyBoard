"""异步运行时配置。"""

import sys


def configure_async_runtime() -> str:
    """非 Windows 使用 uvloop，Windows 或不可用时回退 asyncio。"""
    if sys.platform == "win32":
        return "asyncio"

    try:
        import uvloop
    except ImportError:
        return "asyncio"

    uvloop.install()
    return "uvloop"

