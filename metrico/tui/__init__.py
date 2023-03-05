from metrico.core import MetricoCore
from metrico.tui.app import MetricoApp


def main():
    metrico = MetricoCore.default()
    metrico_app = MetricoApp(metrico)
    metrico_app.run()
