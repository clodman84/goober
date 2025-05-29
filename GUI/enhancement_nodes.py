import copy
import logging
from typing import Callable

import dearpygui.dearpygui as dpg
from PIL import ImageEnhance

from Core import Image

from .graph_abc import Node

logger = logging.getLogger("GUI.InspectNodes")


class EnhanceNode(Node):
    def __init__(
        self,
        label: str,
        parent: str | int,
        update_hook: Callable = lambda: None,
        enhancement: Callable = lambda: None,
        default_value=0,
    ):
        super().__init__(label, parent, update_hook)
        self.image_attribute = self.add_attribute(
            label="Image", attribute_type=dpg.mvNode_Attr_Input
        )
        self.image_output_attribute = self.add_attribute(
            label="Out", attribute_type=dpg.mvNode_Attr_Output
        )
        with dpg.child_window(parent=self.image_attribute, width=100, height=30):
            self.slider = dpg.add_input_float(
                default_value=default_value, callback=self.update_hook
            )
        self.enhancement = enhancement

    def validate_input(self, edge, attribute_id) -> bool:
        # only permitting a single connection
        if self.input_attributes[self.image_attribute]:
            logger.warning(
                "Invalid! You can only connect one image node to preview node"
            )
            return False
        return True

    def process(self):
        if self.input_attributes[self.image_attribute]:
            edge = self.input_attributes[self.image_attribute][0]
            image: Image = edge.data
            enhancer = self.enhancement(copy.deepcopy(image.raw_image))
            factor = dpg.get_value(self.slider)
            updated_image = enhancer.enhance(factor=factor)

            image = Image.from_raw_image(updated_image, (200, 200), (600, 600))

            for edge in self.output_attributes[self.image_output_attribute]:
                edge.data = image
                logger.debug(f"Populated edge {edge.id} with image from {self.id}")


class ColorBalance(EnhanceNode):
    def __init__(
        self,
        parent: str | int,
        update_hook: Callable = lambda: None,
        enhancement=ImageEnhance.Color,
        default_value=1,
        label="Color Balance",
    ):
        super().__init__(label, parent, update_hook, enhancement, default_value)


class Contrast(EnhanceNode):
    def __init__(
        self,
        parent: str | int,
        update_hook: Callable = lambda: None,
        enhancement=ImageEnhance.Contrast,
        default_value=1,
        label="Contrast",
    ):
        super().__init__(label, parent, update_hook, enhancement, default_value)


class Sharpness(EnhanceNode):
    def __init__(
        self,
        parent: str | int,
        update_hook: Callable = lambda: None,
        enhancement=ImageEnhance.Sharpness,
        default_value=1,
        label="Sharpness",
    ):
        super().__init__(label, parent, update_hook, enhancement, default_value)


class Brightness(EnhanceNode):
    def __init__(
        self,
        parent: str | int,
        update_hook: Callable = lambda: None,
        enhancement=ImageEnhance.Brightness,
        default_value=1,
        label="Brightness",
    ):
        super().__init__(label, parent, update_hook, enhancement, default_value)
