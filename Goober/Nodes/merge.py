import logging
from typing import Callable

from dearpygui import dearpygui as dpg

from Goober.Core import Image, merge
from Goober.Nodes import Node

logger = logging.getLogger("GUI.Merge")


class Merge(Node):
    def __init__(self, label: str, parent: str | int, update_hook: Callable):
        super().__init__(label, parent, update_hook)
        self.image_attribute = self.add_attribute(
            label="Image", attribute_type=dpg.mvNode_Attr_Input
        )
        self.image_output_attribute = self.add_attribute(
            label="Out", attribute_type=dpg.mvNode_Attr_Output
        )
        dpg.add_text(
            "Merely adds channels together", wrap=100, parent=self.image_attribute
        )

    def process(self, is_final=False):
        super().process(is_final)
        images = (
            edge.data.raw_image for edge in self.input_attributes[self.image_attribute]
        )
        out = Image("N/A", merge(images), (600, 600), (200, 200))
        for edge in self.output_attributes[self.image_output_attribute]:
            edge.data = out
            logger.debug(f"Populated edge {edge.id} with image from {self.id}")
