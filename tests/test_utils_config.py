from pathlib import Path

from metrico.schemas import DatabaseConfig
from metrico.utils.config import ConfigMixin, MetricoConfig

config_path = Path(__file__).parent / "config.toml"


class DummyMixinClass(ConfigMixin):
    ...


def check_default_config(config: MetricoConfig):
    assert isinstance(config, MetricoConfig)
    assert isinstance(config.hunters, dict)
    assert isinstance(config.triggers, dict)
    assert isinstance(config.db, DatabaseConfig)
    assert isinstance(config.db.url, str)
    assert config.db.url == "sqlite:///database.db"


def test_default_config():
    config = MetricoConfig()
    check_default_config(config)


def test_default_config_load():
    config = MetricoConfig.load()
    check_default_config(config)
    for path in ["23fad", Path("1d12d213c54"), None]:
        config = MetricoConfig.load(path)
        check_default_config(config)


def test_config_load():
    config = MetricoConfig.load(config_path)
    assert isinstance(config, MetricoConfig)
    assert config.db.url == "sqlite://"


def test_config_dict():
    config = MetricoConfig(triggers={"dummy": {"cls": "class", "config": {"foo": "foo", "bar": 42}}})
    check_default_config(config)
    assert len(config.triggers) == 1
    assert config.triggers["dummy"].cls == "class"
    assert config.triggers["dummy"].config["foo"] == "foo"
    assert config.triggers["dummy"].config["bar"] == 42

    config_2 = MetricoConfig()
    assert len(config_2.triggers) == 0

    config_3 = MetricoConfig(**dict(config))
    config_3 = MetricoConfig()
    config_3.parse_obj(config)
    print(config.dict())
    print(config_3)
    # assert len(config_3.triggers) == 1


def test_config_mixin():
    obj_1 = DummyMixinClass()
    check_default_config(obj_1.metrico_config)

    obj_2 = DummyMixinClass(config=obj_1.metrico_config)
    check_default_config(obj_2.metrico_config)

    obj = DummyMixinClass.load(config_path)
    assert isinstance(obj.metrico_config, MetricoConfig)
    assert obj.metrico_config.db.url == "sqlite://"

    obj = DummyMixinClass(filename=config_path)
    assert isinstance(obj.metrico_config, MetricoConfig)
    assert obj.metrico_config.db.url == "sqlite://"


test_config_dict()
