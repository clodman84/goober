import logging
import functools
import time

from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Literal

import dearpygui.dearpygui as dpg

from Goober.Core import natural_time

logger = logging.getLogger("GUI.GraphABC")


@dataclass
class Edge:
    id: str | int
    data: Any
    input: "Node"
    output: "Node"
    input_attribute_id: str | int
    output_attribute_id: str | int

    def connect(self):
        if self.output.validate_input(
            self, self.input_attribute_id
        ) and self.input.validate_output(self, self.output_attribute_id):
            self.input.add_output(self, self.input_attribute_id)
            self.output.add_input(self, self.output_attribute_id)
            logger.debug(f"Connected {self.input} to {self.output} via {self}")
            return
        logger.warning(f"Failed to connect {self.input} to {self.output} via {self}")
        dpg.delete_item(self.id)

    def disconnect(self):
        # DO NOT CHANGE THE ORDER IN WHICH THESE FUNCTIONS ARE CALLED
        self.input.remove_output(self, self.input_attribute_id)
        self.output.remove_input(self, self.output_attribute_id)
        dpg.delete_item(self.id)


def update_exec_time(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        dpg.show_item(self.loading)
        start = time.perf_counter()
        result = func(self, *args, **kwargs)
        end = time.perf_counter()
        dpg.hide_item(self.loading)
        dpg.set_value(self.processing_time, natural_time(end - start))
        return result

    return wrapper


class TimedMeta(ABCMeta):
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)

        # Wrap all methods that override abstract ones
        for base in bases:
            for attr_name, attr_val in base.__dict__.items():
                if getattr(attr_val, "__isabstractmethod__", False):
                    if attr_name in namespace:
                        method = getattr(cls, attr_name)
                        setattr(cls, attr_name, update_exec_time(method))


class Node(ABC, metaclass=TimedMeta):
    """
    Node do the processing, Edges store the data
    """

    def __init__(
        self, label: str, parent: str | int, update_hook: Callable = lambda: None
    ):
        self.id = dpg.add_node(label=label, parent=parent)
        static = dpg.add_node_attribute(
            attribute_type=dpg.mvNode_Attr_Static, parent=self.id
        )
        self.status_group = dpg.add_group(horizontal=True, parent=static)

        dpg.add_button(
            label="Close",
            callback=self.delete,
            parent=self.status_group,
        )

        self.processing_time = dpg.add_text("", parent=self.status_group)
        self.loading = dpg.add_text("(>_<)", parent=self.status_group, show=False)
        self.label = label
        self.parent = parent
        self.input_attributes: dict[str | int, list[Edge]] = {}
        self.output_attributes: dict[str | int, list[Edge]] = {}
        self.update_hook = update_hook
        self.state: Literal[0, 1] = 0

    def delete(self):
        pass

    @abstractmethod
    @update_exec_time
    def process(self, is_final=False):
        """
        It's only job is to populate all output edges
        """
        pass

    def add_attribute(self, label, attribute_type):
        attribute_id = dpg.add_node_attribute(
            parent=self.id, label=label, attribute_type=attribute_type
        )
        if attribute_type == dpg.mvNode_Attr_Input:
            self.input_attributes[attribute_id] = []
        elif attribute_type == dpg.mvNode_Attr_Output:
            self.output_attributes[attribute_id] = []
        logger.debug(
            f"Attribute lists for {self.label} is {self.input_attributes} and {self.output_attributes}"
        )
        return attribute_id

    def add_input(self, edge: Edge, attribute_id):
        self.input_attributes[attribute_id].append(edge)
        self.update()

    def add_output(self, edge: Edge, attribute_id):
        self.activate()
        self.output_attributes[attribute_id].append(edge)

    def remove_input(self, edge: Edge, attribute_id):
        self.activate()
        self.input_attributes[attribute_id].remove(edge)

    def remove_output(self, edge: Edge, attribute_id):
        self.output_attributes[attribute_id].remove(edge)
        self.update()

    def update(self):
        self.activate()
        self.update_hook()

    def activate(self):
        self.state = 1
        logger.debug(str(self))
        for attribute in self.output_attributes.values():
            for edge in attribute:
                edge.output.activate()

    def validate_input(self, edge, attribute_id) -> bool:
        return True

    def validate_output(self, edge, attribute_id) -> bool:
        return True

    def __str__(self):
        return f"{self.label} {id(self)} state: {self.state}"


class InspectNode(Node):
    def __init__(self, label: str, parent: str | int, update_hook: Callable):
        super().__init__(label, parent, update_hook)
