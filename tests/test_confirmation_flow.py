"""Test the one-time credential confirmation form with minimal HA stand-ins."""

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/garmin_data_bridge"


class FakeMarker:
    """Simulate a Voluptuous field marker and its default."""

    def __init__(self, name, default=None):
        self.name = name
        self.default = default


class FakeSchema:
    """Expose the form schema for assertions."""

    def __init__(self, schema):
        self.schema = schema


class FakeConfigFlow:
    """Support config-flow construction and returns."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    def async_abort(self, **kwargs):
        return {"type": "abort", **kwargs}


@pytest.fixture
def config_flow_module(monkeypatch):
    """Load the production flow using lightweight stubs, not a fake flow body."""
    pkg = ModuleType("garmin_test_fixture")
    pkg.__path__ = [str(ROOT)]
    monkeypatch.setitem(sys.modules, pkg.__name__, pkg)

    voluptuous = ModuleType("voluptuous")
    voluptuous.Schema = FakeSchema
    voluptuous.Optional = FakeMarker
    voluptuous.Required = FakeMarker
    monkeypatch.setitem(sys.modules, "voluptuous", voluptuous)

    homeassistant = ModuleType("homeassistant")
    config_entries = ModuleType("homeassistant.config_entries")
    config_entries.ConfigFlow = FakeConfigFlow
    config_entries.OptionsFlow = type("FakeOptionsFlow", (), {})
    config_entries.ConfigEntry = object
    homeassistant.config_entries = config_entries
    monkeypatch.setitem(sys.modules, "homeassistant", homeassistant)
    monkeypatch.setitem(sys.modules, "homeassistant.config_entries", config_entries)

    core = ModuleType("homeassistant.core")
    core.callback = lambda function: function
    monkeypatch.setitem(sys.modules, "homeassistant.core", core)

    data_entry_flow = ModuleType("homeassistant.data_entry_flow")
    data_entry_flow.FlowResult = dict
    monkeypatch.setitem(sys.modules, "homeassistant.data_entry_flow", data_entry_flow)

    helpers = ModuleType("homeassistant.helpers")
    selector = SimpleNamespace(
        TextSelectorConfig=lambda **kwargs: kwargs,
        TextSelector=lambda config: {"text": config},
        EntitySelectorConfig=lambda **kwargs: kwargs,
        EntitySelector=lambda config: {"entity": config},
    )
    helpers.selector = selector
    monkeypatch.setitem(sys.modules, "homeassistant.helpers", helpers)

    module_name = "garmin_test_fixture.config_flow"
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "config_flow.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


def test_confirmation_is_copyable_but_only_the_digest_is_persisted(config_flow_module):
    """Generated plaintext must be visible in a text field, never stored."""
    flow = config_flow_module.GarminDataBridgeConfigFlow()
    flow._profile = "My Garmin"
    flow._entities = ["sensor.outside"]
    flow._token = "random-generated-secret"

    form = asyncio.run(flow.async_step_confirm())
    assert form["type"] == "form"
    field, selector = next(iter(form["data_schema"].schema.items()))
    assert field.name == "copy_token"
    assert field.default == flow._token
    assert selector == {"text": {"autocomplete": "off"}}
    assert "description_placeholders" not in form

    created = asyncio.run(flow.async_step_confirm({"copy_token": flow._token}))
    assert created["type"] == "create_entry"
    assert created["data"]["token_digest"] == config_flow_module.token_digest(
        flow._token
    )
    assert flow._token not in str(created["data"])
    assert "copy_token" not in created["data"]


def test_modified_token_is_rejected(config_flow_module):
    """Accidentally editing the copyable field may not create a bad profile."""
    flow = config_flow_module.GarminDataBridgeConfigFlow()
    flow._profile = "My Garmin"
    flow._entities = ["sensor.outside"]
    flow._token = "random-generated-secret"

    result = asyncio.run(flow.async_step_confirm({"copy_token": "wrong-token"}))
    assert result["type"] == "form"
    assert result["errors"] == {"base": "token_modified"}
    field = next(iter(result["data_schema"].schema))
    assert field.default == flow._token
