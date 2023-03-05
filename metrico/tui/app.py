from typing import Type

from textual.app import App, ComposeResult, CSSPathType
from textual.driver import Driver
from textual.widgets import Footer

from metrico.core import MetricoCore

from .widgets import BasicQuery  # type: ignore


class MetricoApp(App):
    def __init__(self, metrico: MetricoCore, driver_class: Type[Driver] | None = None, css_path: CSSPathType | None = None, watch_css: bool = False):
        self.metrico = metrico
        super().__init__(driver_class, css_path, watch_css)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield BasicQuery()
        yield Footer()
