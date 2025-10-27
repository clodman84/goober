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
        with dpg.group(parent=self.image_attribute, width=200, height=250):
            dpg.add_text("Shadows")
            self.red_shadows = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.red_shadows, "red")
            self.green_shadows = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.green_shadows, "green")
            self.blue_shadows = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.blue_shadows, "blue")
            dpg.add_text("Midtones")
            self.red_midtones = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.red_midtones, "red")
            self.green_midtones = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.green_midtones, "green")
            self.blue_midtones = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.blue_midtones, "blue")
            dpg.add_text("Highlights")
            self.red_highlights = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.red_highlights, "red")
            self.green_highlights = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.green_highlights, "green")
            self.blue_highlights = dpg.add_colormap_slider(
                default_value=0.5, callback=self.update, width=170
            )
            dpg.bind_colormap(self.blue_highlights, "blue")
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
    def process(self, is_final=True):
        if self.input_attributes[self.image_attribute]:
            edge = self.input_attributes[self.image_attribute][0]
            image: Image = edge.data
            preserve = dpg.get_value(self.preserve_luminance)

            dr_s = int(dpg.get_value(self.red_shadows) * 200 - 100)
            dg_s = int(dpg.get_value(self.green_shadows) * 200 - 100)
            db_s = int(dpg.get_value(self.blue_shadows) * 200 - 100)

            dr_m = int(dpg.get_value(self.red_midtones) * 200 - 100)
            dg_m = int(dpg.get_value(self.green_midtones) * 200 - 100)
            db_m = int(dpg.get_value(self.blue_midtones) * 200 - 100)

            dr_h = int(dpg.get_value(self.red_highlights) * 200 - 100)
            dg_h = int(dpg.get_value(self.green_highlights) * 200 - 100)
            db_h = int(dpg.get_value(self.blue_highlights) * 200 - 100)

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
