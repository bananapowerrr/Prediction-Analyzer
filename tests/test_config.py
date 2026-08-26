import json
import os

import pytest

from core.config import Config


def test_init_defaults_empty():
    cfg = Config()
    assert cfg.as_dict() == {}


def test_init_with_defaults():
    cfg = Config({"a": 1, "b": "x"})
    assert cfg.as_dict() == {"a": 1, "b": "x"}


def test_get_returns_value():
    cfg = Config({"key": "value"})
    assert cfg.get("key") == "value"


def test_get_returns_default_when_missing():
    cfg = Config()
    assert cfg.get("missing", "fallback") == "fallback"
    assert cfg.get("missing") is None


def test_set_and_get():
    cfg = Config()
    cfg.set("name", "agent")
    assert cfg.get("name") == "agent"


def test_set_overwrites_existing():
    cfg = Config({"k": 1})
    cfg.set("k", 2)
    assert cfg.get("k") == 2


def test_update_merges_values():
    cfg = Config({"a": 1, "b": 2})
    cfg.update({"b": 20, "c": 30})
    assert cfg.as_dict() == {"a": 1, "b": 20, "c": 30}


def test_as_dict_returns_copy():
    cfg = Config({"a": 1})
    d = cfg.as_dict()
    d["a"] = 99
    assert cfg.get("a") == 1


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "config.json")
    cfg = Config({"a": 1, "b": [1, 2], "c": {"nested": True}})
    cfg.save(path)
    assert os.path.exists(path)

    loaded = Config()
    loaded.load(path)
    assert loaded.as_dict() == {"a": 1, "b": [1, 2], "c": {"nested": True}}


def test_save_creates_directories(tmp_path):
    path = str(tmp_path / "nested" / "dir" / "config.json")
    cfg = Config({"x": 1})
    cfg.save(path)
    assert os.path.exists(path)


def test_load_missing_file_is_noop(tmp_path):
    path = str(tmp_path / "does_not_exist.json")
    cfg = Config({"keep": "me"})
    cfg.load(path)
    assert cfg.as_dict() == {"keep": "me"}


def test_load_preserves_existing_keys(tmp_path):
    path = str(tmp_path / "config.json")
    cfg = Config({"a": 1, "b": 2})
    cfg.save(path)

    cfg2 = Config({"b": 99, "c": 3})
    cfg2.load(path)
    assert cfg2.as_dict() == {"b": 2, "c": 3, "a": 1}


def test_load_ignores_non_dict_content(tmp_path):
    path = str(tmp_path / "config.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps([1, 2, 3]))
    cfg = Config({"keep": "me"})
    cfg.load(path)
    assert cfg.as_dict() == {"keep": "me"}


def test_load_invalid_json_raises(tmp_path):
    path = str(tmp_path / "config.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    cfg = Config()
    with pytest.raises(json.JSONDecodeError):
        cfg.load(path)


def test_save_is_valid_json(tmp_path):
    path = str(tmp_path / "config.json")
    cfg = Config({"k": "v"})
    cfg.save(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {"k": "v"}


def test_save_preserves_unicode(tmp_path):
    path = str(tmp_path / "config.json")
    cfg = Config({"label": "привет"})
    cfg.save(path)
    loaded = Config()
    loaded.load(path)
    assert loaded.get("label") == "привет"
