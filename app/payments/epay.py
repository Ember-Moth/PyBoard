"""EPay 支付网关实现。"""

import hashlib
import hmac
import urllib.parse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from app.payments.base import PaymentGateway, PaymentNotifyResult, PaymentRequest


class EPay(PaymentGateway):
    """EPay 易支付网关。"""

    gateway = "EPay"
    label = "易支付"
    aliases = ("epay",)
    required_config = ("url", "pid", "key")

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url", "")
        self.pid = config.get("pid", "")
        self.key = config.get("key", "")
        self.pay_type = config.get("type", "")

    @classmethod
    def form(cls, config: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
        """返回 EPay 配置表单结构。"""
        form = {
            "url": {
                "label": "URL",
                "description": "",
                "type": "input",
            },
            "pid": {
                "label": "PID",
                "description": "",
                "type": "input",
            },
            "key": {
                "label": "KEY",
                "description": "",
                "type": "input",
            },
            "type": {
                "label": "TYPE",
                "description": "支付类型，如: alipay, wxpay, qqpay",
                "type": "input",
            },
        }
        if config:
            for key, value in config.items():
                if key in form:
                    form[key]["value"] = value
        return form

    def pay(self, request: PaymentRequest) -> dict[str, Any]:
        """生成支付参数。

        Args:
            request: 标准支付请求

        Returns:
            {"type": 1, "data": 支付跳转URL}
        """
        params = {
            "money": self._cents_to_money(request.total_amount),
            "name": request.trade_no,
            "notify_url": request.notify_url,
            "return_url": request.return_url,
            "out_trade_no": request.trade_no,
            "pid": self.pid,
        }

        if self.pay_type:
            params["type"] = self.pay_type

        # 生成签名
        sign = self._generate_sign(params)
        params["sign"] = sign
        params["sign_type"] = "MD5"

        pay_url = f"{self.url}/submit.php?{urllib.parse.urlencode(params)}"

        return {"type": 1, "data": pay_url}

    def verify_notify(self, params: dict[str, Any]) -> PaymentNotifyResult:
        """验证回调签名。

        Args:
            params: 回调参数

        Returns:
            支付回调标准结果
        """
        sign = params.get("sign", "")

        # 移除 sign 和 sign_type
        verify_params = {k: v for k, v in params.items() if k not in ("sign", "sign_type")}

        generated_sign = self._generate_sign(verify_params)

        if not self._hash_equals(generated_sign, sign):
            return PaymentNotifyResult(success=False)

        if self.pid and str(params.get("pid", "")) != str(self.pid):
            return PaymentNotifyResult(success=False)

        # 检查交易状态
        trade_status = params.get("trade_status", "")
        if trade_status != "TRADE_SUCCESS":
            return PaymentNotifyResult(success=False)

        out_trade_no = params.get("out_trade_no", "")
        trade_no = params.get("trade_no", "")
        paid_amount = self._money_to_cents(params.get("money"))
        if not out_trade_no or not trade_no or paid_amount is None:
            return PaymentNotifyResult(success=False)

        return PaymentNotifyResult(
            success=True,
            trade_no=out_trade_no,
            callback_no=trade_no,
            paid_amount=paid_amount,
        )

    def _generate_sign(self, params: dict[str, Any]) -> str:
        """按 EPay/PHP 版规则生成 MD5 签名。"""
        sign_params = {
            key: value
            for key, value in params.items()
            if key not in ("sign", "sign_type") and value not in ("", None)
        }
        sorted_params = sorted(sign_params.items())
        param_str = urllib.parse.urlencode(dict(sorted_params))
        param_str = self._php_stripslashes(urllib.parse.unquote_plus(param_str))
        sign_str = param_str + self.key
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    def _hash_equals(self, a: str, b: str) -> bool:
        """安全的字符串比较，防止时序攻击。"""
        return hmac.compare_digest(a, b)

    def _money_to_cents(self, money: Any) -> int | None:
        """将 EPay 回调里的元金额转换为分。"""
        try:
            amount = Decimal(str(money))
        except (InvalidOperation, ValueError):
            return None
        cents = (amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if cents < 0:
            return None
        return int(cents)

    def _cents_to_money(self, cents: int) -> str:
        """将分转换为 EPay 使用的元字符串，格式对齐 PHP http_build_query。"""
        amount = Decimal(cents) / Decimal("100")
        return format(amount.normalize(), "f")

    def _php_stripslashes(self, value: str) -> str:
        """模拟 PHP stripslashes 对签名字符串的处理。"""
        result: list[str] = []
        index = 0
        while index < len(value):
            char = value[index]
            if char == "\\" and index + 1 < len(value) and value[index + 1] in ("\\", "'", '"'):
                index += 1
                char = value[index]
            result.append(char)
            index += 1
        return "".join(result)
