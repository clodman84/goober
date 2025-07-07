import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Literal

import dearpygui.dearpygui as dpg

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


class Node(ABC):
    """
    Node do the processing, Edges store the data
    """

    def __init__(
        self, label: str, parent: str | int, update_hook: Callable = lambda: None
    ):
        self.id = dpg.add_node(label=label, parent=parent)
        self.label = label
        self.parent = parent
        self.input_attributes: dict[str | int, list[Edge]] = {}
        self.output_attributes: dict[str | int, list[Edge]] = {}
        self.update_hook = update_hook
        self.state: Literal[0, 1] = 0

    @abstractmethod
    def process(self, is_final=False):
        """
        It's only job is to populate all output edges
        """

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
        # add an action saving feature here
        self.activate()
        self.update_hook()

    def activate(self):
        self.state = 1
        logger.debug(f"{self} state changed to 1")
        for attribute in self.output_attributes.values():
            for edge in attribute:
                edge.output.activate()

    def validate_input(self, edge, attribute_id) -> bool:
        return True

    def validate_output(self, edge, attribute_id) -> bool:
        return True
