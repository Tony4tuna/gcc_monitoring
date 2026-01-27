"""Shared layout helpers for data-heavy pages."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from nicegui import ui

__all__ = ["data_grid_shell", "DataGridShell"]

_CSS_INJECTED = False


def _ensure_css() -> None:
    global _CSS_INJECTED
    if _CSS_INJECTED:
        return

    ui.add_head_html(
        """
    <style>
      .gcc-data-table thead th,
      .gcc-data-table tbody td {
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
      }
      body.light .gcc-data-table thead th,
      body.light .gcc-data-table tbody td {
        border: 1px solid rgba(0, 0, 0, 0.18) !important;
      }
      .gcc-data-table thead th {
        position: sticky;
        top: 0;
        z-index: 2;
        background: var(--card) !important;
      }
            .gcc-data-scroll {
                display: flex;
                flex-direction: column;
                padding: 0;
            }
            .gcc-data-scroll .q-table__container {
                height: 100% !important;
                max-height: none !important;
                display: flex !important;
                flex-direction: column !important;
                background: transparent !important;
                border: none !important;
            }
            .gcc-data-scroll .q-table__middle {
                flex: 1 !important;
                min-height: 0 !important;
                max-height: none !important;
                overflow-y: auto !important;
                overflow-x: auto !important;
            }
            .gcc-data-scroll .q-table__card {
                box-shadow: none !important;
                background: transparent !important;
            }
      .gcc-data-empty {
        padding: 12px 16px;
        color: var(--muted);
        font-size: 14px;
      }
    </style>
    """
    )
    _CSS_INJECTED = True


class DataGridShell:
    """Helper object returned by :func:`data_grid_shell`."""

    def __init__(self, *, tight: bool, height: Optional[str], max_height: Optional[str], outlined: bool) -> None:
        _ensure_css()
        gap_class = "gap-3" if tight else "gap-4"
        root = ui.column().classes(f"gcc-data-shell {gap_class} w-full flex-1 min-h-0 items-stretch overflow-hidden")
        styles: list[str] = []
        if height:
            styles.append(f"height: {height}")
        if max_height:
            styles.append(f"max-height: {max_height}")
        if styles:
            root.style("; ".join(styles))
        self._root = root
        self._outlined = outlined

    def __enter__(self) -> "DataGridShell":
        self._root.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._root.__exit__(exc_type, exc, tb)

    @property
    def container(self):
        return self._root

    @contextmanager
    def toolbar(self) -> Generator[None, None, None]:
        column = ui.column().classes("gcc-data-toolbar w-full gap-3 flex-shrink-0")
        if self._outlined:
            column.style("border: 1px solid var(--border); border-radius: 12px; padding: 16px; background: var(--card);")
        else:
            column.style("padding: 8px 0; gap: 12px;")
        with column:
            yield

    @contextmanager
    def body(self) -> Generator[None, None, None]:
        column = ui.column().classes("gcc-data-surface flex-1 min-h-0 overflow-hidden")
        if self._outlined:
            column.style("border: 1px solid var(--border); border-radius: 12px; background: var(--card); padding: 0;")
        else:
            column.style("background: transparent; padding: 0;")
        with column:
            with ui.element().classes("gcc-data-scroll flex-1 min-h-0 overflow-auto"):
                yield


@contextmanager
def data_grid_shell(*, tight: bool = False, height: Optional[str] = None, max_height: Optional[str] = None, outlined: bool = False) -> Generator[DataGridShell, None, None]:
    """Reusable two-section layout for data-heavy views.

    Parameters
    ----------
    tight: bool
        Reduce vertical gaps; handy for dense UIs.
    height: str | None
        Optional CSS height expression to pin the shell.
    max_height: str | None
        Optional CSS max-height expression.
    """

    shell = DataGridShell(tight=tight, height=height, max_height=max_height, outlined=outlined)
    with shell:
        yield shell
