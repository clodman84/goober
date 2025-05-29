import logging
from typing import Callable

import dearpygui.dearpygui as dpg

from Core import Image

from .graph_abc import Node

logger = logging.getLogger("GUI.ImageNodes")


class ImageNode(Node):
    def __init__(
        self, label: str, parent: str | int, image: Image, update_hook: Callable
    ):
        super().__init__(label, parent, update_hook=update_hook)
        self.image = image
        with dpg.texture_registry():
            dpg.add_dynamic_texture(
                200,
                200,
                default_value=image.thumbnail[3],
                tag=f"{self.id}_image",
            )
            logger.debug("Added entry to texture_registry")
        self.image_attribute = self.add_attribute(
            label="Image", attribute_type=dpg.mvNode_Attr_Output
        )
        with dpg.child_window(width=200, height=200, parent=self.image_attribute):
            dpg.add_image(f"{self.id}_image")
            logger.debug("Added image to node")

    def process(self):
        # put the image in all connected output edges
        for edge in self.output_attributes[self.image_attribute]:
            edge.data = self.image
            logger.debug(f"Populated edge {edge.id} with image from {self.id}")
