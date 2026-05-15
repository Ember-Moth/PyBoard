"""模板渲染引擎 —— 基于 Jinja2，支持动态内容生成。

使用方式：
    from app.utils.template import render

    html = render("mail/welcome", user_name="张三", confirm_url="...")
    纯文本 = render("mail/welcome.txt", user_name="张三")
"""

import os

from jinja2 import Environment, FileSystemLoader

# 模板根目录
_template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

# Jinja2 环境（全局单例）
_env = Environment(
    loader=FileSystemLoader(_template_dir),
    autoescape=True,  # HTML 自动转义
    enable_async=True,  # 支持异步渲染
)

# 自定义过滤器：换行 → <br>
_env.filters["nl2br"] = lambda text: text.replace("\n", "<br>")


def render(template_name: str, **context: object) -> str:
    """同步渲染模板。

    Args:
        template_name: 模板路径（相对于 templates/ 目录），不含扩展名时自动补 .html
        **context: 模板变量

    Returns:
        渲染后的字符串
    """
    resolved = _resolve_name(template_name)
    template = _env.get_template(resolved)
    return template.render(**context)


async def render_async(template_name: str, **context: object) -> str:
    """异步渲染模板（支持模板内 await）。

    Args:
        template_name: 模板路径
        **context: 模板变量

    Returns:
        渲染后的字符串
    """
    resolved = _resolve_name(template_name)
    template = _env.get_template(resolved)
    return await template.render_async(**context)


def _resolve_name(name: str) -> str:
    """模板名不以 .html/.txt 结尾时，自动补 .html。"""
    if name.endswith((".html", ".txt", ".jinja2", ".j2")):
        return name
    return f"{name}.html"
