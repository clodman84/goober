import logging
from typing import Callable

import dearpygui.dearpygui as dpg
from line_profiler import profile

from Goober.Core import Image, colour_balance

from .graph_abc import Node

logger = logging.getLogger("GUI.ColourBalance")


class ColourBalance(Node):
    def __init__(
        self,
        label: str,
        parent: str | int,
        update_hook: Callable = lambda: None,
    ):
        super().__init__(label, parent, update_hook)
        self.image_attribute = self.add_attribute(
            label="Image", attribute_type=dpg.mvNode_Attr_Input
        )
        self.image_output_attribute = self.add_attribute(
            label="Out", attribute_type=dpg.mvNode_Attr_Output
        )
        with dpg.child_window(parent=self.image_attribute, width=200, height=250):
            dpg.add_text("Shadows")
            # TODO: replace these with colourmap_sliders
            self.red_shadows = dpg.add_slider_int(
                label="Red",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.green_shadows = dpg.add_slider_int(
                label="Green",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.blue_shadows = dpg.add_slider_int(
                label="Blue",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            dpg.add_text("Midtones")
            self.red_midtones = dpg.add_slider_int(
                label="Red",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.green_midtones = dpg.add_slider_int(
                label="Green",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.blue_midtones = dpg.add_slider_int(
                label="Blue",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            dpg.add_text("Highlights")
            self.red_highlights = dpg.add_slider_int(
                label="Red",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.green_highlights = dpg.add_slider_int(
                label="Green",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.blue_highlights = dpg.add_slider_int(
                label="Blue",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.preserve_luminance = dpg.add_checkbox(
                label="Preserve Luminance", callback=self.update
            )

    def validate_input(self, edge, attribute_id) -> bool:
        # only permitting a single connection
        if self.input_attributes[self.image_attribute]:
            logger.warning(
                "Invalid! You can only connect one image node to preview node"
            )
            return False
        return True

    @profile
    def process(self):
        if self.input_attributes[self.image_attribute]:
            edge = self.input_attributes[self.image_attribute][0]
            image: Image = edge.data
            preserve = dpg.get_value(self.preserve_luminance)

            dr_s = dpg.get_value(self.red_shadows)
            dg_s = dpg.get_value(self.green_shadows)
            db_s = dpg.get_value(self.blue_shadows)

            dr_m = dpg.get_value(self.red_midtones)
            dg_m = dpg.get_value(self.green_midtones)
            db_m = dpg.get_value(self.blue_midtones)

            dr_h = dpg.get_value(self.red_highlights)
            dg_h = dpg.get_value(self.green_highlights)
            db_h = dpg.get_value(self.blue_highlights)

            updated_image = colour_balance(
                image.raw_image,
                [dr_s, dg_s, db_s],
                [dr_m, dg_m, db_m],
                [dr_h, dg_h, db_h],
                preserve,
            )
            image = Image("NA", updated_image, (600, 600), (200, 200))

            for edge in self.output_attributes[self.image_output_attribute]:
                edge.data = image
                logger.debug(f"Populated edge {edge.id} with image from {self.id}")
