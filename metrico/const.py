from pathlib import Path

DEFAULT_FILENAME: Path = Path("metrico.toml")
DEFAULT_FILENAMES: list[Path] = [
    DEFAULT_FILENAME,
    Path("/etc/metrico/config.toml"),
]
