import itertools
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dearpygui.dearpygui as dpg

import Application
from Application import Image, ImageManager

logger = logging.getLogger("GUI.Editor")


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
        logger.debug(f"Failed to connect {self.input} to {self.output} via {self}")
        dpg.delete_item(self.id)

    def disconnect(self):
        self.input.remove_output(self, self.input_attribute_id)
        self.output.remove_input(self, self.output_attribute_id)
        dpg.delete_item(self.id)


class Node(ABC):
    def __init__(self, label: str, parent: str | int):
        self.id = dpg.add_node(label=label, parent=parent)
        self.label = label
        self.parent = parent
        self.input_attributes: dict[str | int, list[Edge]] = {}
        self.output_attributes: dict[str | int, list[Edge]] = {}

    @abstractmethod
    def process(self):
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

    def add_output(self, edge: Edge, attribute_id):
        self.output_attributes[attribute_id].append(edge)

    def remove_input(self, edge: Edge, attribute_id):
        self.input_attributes[attribute_id].remove(edge)

    def remove_output(self, edge: Edge, attribute_id):
        self.output_attributes[attribute_id].remove(edge)

    def validate_input(self, edge, attribute_id) -> bool:
        return True

    def validate_output(self, edge, attribute_id) -> bool:
        return True


class HistogramNode(Node):
    def __init__(self, label: str, parent: str | int):
        super().__init__(label, parent)
        self.image_attribute = self.add_attribute(
            label="Image", attribute_type=dpg.mvNode_Attr_Input
        )
        with dpg.child_window(parent=self.image_attribute, width=200, height=200):
            # TODO: Make this a graph (RGB)
            with dpg.plot(height=-1, width=-1, no_inputs=True):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Value", no_label=True)
                dpg.add_plot_axis(
                    dpg.mvYAxis,
                    label="Count",
                    tag=f"{self.id}_yaxis",
                    no_label=True,
                    auto_fit=True,
                )
                dpg.add_line_series(
                    [i for i in range(256)],
                    [
                        0.0,
                    ]
                    * 256,
                    tag=f"{self.id}_R",
                    parent=f"{self.id}_yaxis",
                )
                dpg.add_line_series(
                    [i for i in range(256)],
                    [
                        0.0,
                    ]
                    * 256,
                    tag=f"{self.id}_G",
                    parent=f"{self.id}_yaxis",
                )
                dpg.add_line_series(
                    [i for i in range(256)],
                    [
                        0.0,
                    ]
                    * 256,
                    tag=f"{self.id}_B",
                    parent=f"{self.id}_yaxis",
                )
        logger.debug("Initialised histogram node")

    def process(self):
        # TODO: Imaplement this
        edge = self.input_attributes[self.image_attribute][0]
        image: Image = edge.data
        histogram = Application.get_histogram(image.raw_image)
        dpg.set_value(f"{self.id}_R", [[i for i in range(256)], histogram[0]])
        dpg.set_value(f"{self.id}_G", [[i for i in range(256)], histogram[1]])
        dpg.set_value(f"{self.id}_B", [[i for i in range(256)], histogram[2]])
        logger.debug(f"Processed histogram in histogram node {self.id}")

    def validate_input(self, edge, attribute_id) -> bool:
        # only permitting a single connection
        if self.input_attributes[self.image_attribute]:
            logger.warning(
                "Invalid! You can only connect one image node to histogram node"
            )
            return False
        return True


class ImageNode(Node):
    def __init__(self, label: str, parent: str | int, image: Image):
        super().__init__(label, parent)
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


class EditingWindow:
    def __init__(self, source: list[Path]) -> None:
        self.image_manager = ImageManager.from_file_list(
            source, (600, 600), thumbnail_dimensions=(200, 200)
        )
        self.node_lookup_by_attribute_id = {}
        self.edge_lookup_by_edge_id = {}
        self.adjacency_list: dict[Node, list[Node]] = {}

        with dpg.window(label="Image Editor", width=500, height=500):
            with dpg.menu_bar():
                with dpg.menu(label="Inspect"):
                    dpg.add_menu_item(
                        label="Histogram", callback=self.add_histogram_node
                    )
                with dpg.menu(label="Import"):
                    dpg.add_menu_item(label="Image", callback=self.add_image_node)
                dpg.add_button(label="Evaluate", callback=self.evaluate)
            with dpg.node_editor(
                callback=self.link, delink_callback=self.delink, minimap=True
            ) as self.node_editor:
                pass

    def link(self, sender, app_data):
        id = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
        logger.debug(self.node_lookup_by_attribute_id)

        input: Node = self.node_lookup_by_attribute_id[app_data[0]]
        output: Node = self.node_lookup_by_attribute_id[app_data[1]]

        edge = Edge(id, None, input, output, app_data[0], app_data[1])
        self.edge_lookup_by_edge_id[id] = edge
        self.adjacency_list[input].append(output)
        # TODO: Implement adjacency list
        edge.connect()

    def delink(self, sender, app_data):
        edge = self.edge_lookup_by_edge_id[app_data]
        edge.disconnect()
        self.adjacency_list[edge.input].remove(edge.output)

    def add_node(self, node: Node):
        for attribute in itertools.chain(node.input_attributes, node.output_attributes):
            self.node_lookup_by_attribute_id[attribute] = node
        self.adjacency_list[node] = []

    def add_histogram_node(self):
        node = HistogramNode(label="Histogram", parent=self.node_editor)
        self.add_node(node)

    def add_image_node(self):
        node = ImageNode(
            label="Image", parent=self.node_editor, image=self.image_manager.load(0)
        )
        self.add_node(node)

    def topological_sort(self):
        # kahn's algo
        sorted_list = []

        in_degree = defaultdict(int)
        for node in self.adjacency_list:
            for neighbour in self.adjacency_list[node]:
                in_degree[neighbour] += 1

        logger.debug(f"Computed in_degree: {in_degree}")
        queue = [node for node in self.adjacency_list if in_degree[node] == 0]
        dropped = set()

        logger.debug(f"Source node queue: {queue}")
        # if a node is completely disconnected, we do not give a shit about it
        for node in self.adjacency_list:
            if not self.adjacency_list[node] and not in_degree[node]:
                dropped.add(node)

        while queue:
            node = queue.pop()
            if node in dropped:
                continue
            sorted_list.append(node)
            logger.debug(f"{node}, adjecency - {self.adjacency_list[node]}")
            for neighbour in self.adjacency_list[node]:
                in_degree[neighbour] -= 1
                if in_degree[neighbour] == 0:
                    queue.append(neighbour)

        logger.debug(f"Dropped nodes: {dropped}")
        logger.debug(f"Sorted list: {sorted_list}")

        if len(sorted_list) + len(dropped) != len(self.adjacency_list):
            logger.error("There is a cycle in your graph!!!")
            return False
        else:
            return sorted_list

    def evaluate(self):
        sorted_node_list = self.topological_sort()
