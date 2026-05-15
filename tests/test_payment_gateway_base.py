"""支付网关抽象基类测试。"""

import pytest

from app.payments.base import PaymentGateway, PaymentNotifyResult, PaymentRequest


def test_payment_gateway_base_is_abstract():
    with pytest.raises(TypeError):
        PaymentGateway({})


def test_incomplete_gateway_cannot_be_instantiated():
    class IncompleteGateway(PaymentGateway):
        gateway = "Incomplete"
        label = "Incomplete"

        def pay(self, request: PaymentRequest) -> dict:
            return {"type": 1, "data": "ok"}

    with pytest.raises(TypeError):
        IncompleteGateway({})


def test_complete_gateway_can_be_instantiated():
    class CompleteGateway(PaymentGateway):
        gateway = "Complete"
        label = "Complete"

        def pay(self, request: PaymentRequest) -> dict:
            return {"type": 1, "data": "ok"}

        def verify_notify(self, params: dict) -> PaymentNotifyResult:
            return PaymentNotifyResult(success=True, trade_no="T1", callback_no="C1", paid_amount=100)

    gateway = CompleteGateway({})
    assert gateway.pay(PaymentRequest(trade_no="T1", total_amount=100, notify_url="n", return_url="r")) == {
        "type": 1,
        "data": "ok",
    }
    assert gateway.verify_notify({}).success is True
