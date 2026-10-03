import sys
from types import ModuleType

import pytest

from alfa_omega.data.huggingface_client import create_huggingface_api


def test_client_requires_runtime_token(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="HF_TOKEN"):
        create_huggingface_api()


def test_client_does_not_persist_token(monkeypatch):
    calls = {}
    fake_module = ModuleType("huggingface_hub")

    class FakeApi:
        def __init__(self, **kwargs):
            calls.update(kwargs)

    fake_module.HfApi = FakeApi
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_module)
    monkeypatch.setenv("HF_TOKEN", "test-secret")
    api = create_huggingface_api()

    assert isinstance(api, FakeApi)
    assert calls == {"token": "test-secret"}
