import logging
from typing import Callable

import dearpygui.dearpygui as dpg
from line_profiler import profile

from Core import Image, colour_balance

from .graph_abc import Node

logger = logging.getLogger("GUI.InspectNodes")


class ManualColorBalance(Node):
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
        with dpg.child_window(parent=self.image_attribute, width=200, height=60):
            self.red = dpg.add_slider_int(
                label="Red",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.green = dpg.add_slider_int(
                label="Green",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
            )
            self.blue = dpg.add_slider_int(
                label="Blue",
                default_value=0,
                callback=self.update,
                width=150,
                min_value=-100,
                max_value=100,
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
            dr = dpg.get_value(self.red)
            dg = dpg.get_value(self.green)
            db = dpg.get_value(self.blue)

            updated_image = colour_balance(image.raw_image, dr, dg, db)
            image = Image("NA", updated_image, (600, 600), (200, 200))

            for edge in self.output_attributes[self.image_output_attribute]:
                edge.data = image
                logger.debug(f"Populated edge {edge.id} with image from {self.id}")
