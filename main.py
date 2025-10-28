import logging
from pathlib import Path

import dearpygui.dearpygui as dpg
from dearpygui import demo
from themes import create_gruvbox_dark_theme

import Goober.image_editor
import Goober.utils

logger = logging.getLogger("Core.Main")
import dearpygui.dearpygui as dpg


def main():
    dpg.create_context()
    create_gruvbox_dark_theme()
    dpg.create_viewport(title="ShittyLightroom")
    core_logger = logging.getLogger("Core")
    gui_logger = logging.getLogger("GUI")
    core_logger.setLevel(logging.DEBUG)
    gui_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[{threadName}][{asctime}] [{levelname:<8}] {name}: {message}",
        "%H:%M:%S",
        style="{",
    )

    with dpg.window(tag="Primary Window"):
        with dpg.menu_bar():
            with dpg.menu(label="Tools"):
                dpg.add_menu_item(
                    label="Show Performance Metrics", callback=dpg.show_metrics
                )
            with dpg.menu(label="Dev"):
                dpg.add_menu_item(label="Show GUI Demo", callback=demo.show_demo)
                dpg.add_menu_item(
                    label="Spawn Image Editor",
                    callback=lambda: Goober.image_editor.EditingWindow(
                        [i for i in Path("./Data/18R/").iterdir()]
                    ),
                )

    with dpg.colormap_registry():
        dpg.add_colormap(
            [[0, 255, 255], [255, 0, 0]],
            False,
            tag="red",
        )

        dpg.add_colormap(
            [[255, 0, 255], [0, 255, 0]],
            False,
            tag="green",
        )

        dpg.add_colormap(
            [[255, 255, 0], [0, 0, 255]],
            False,
            tag="blue",
        )

    log = Goober.utils.Logger()
    log.setFormatter(formatter)
    core_logger.addHandler(log)
    gui_logger.addHandler(log)

    dpg.setup_dearpygui()
    dpg.set_primary_window("Primary Window", True)
    dpg.set_viewport_vsync(False)
    dpg.show_viewport(maximized=True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
