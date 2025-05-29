import itertools
import logging
from collections import defaultdict
from pathlib import Path

import dearpygui.dearpygui as dpg

from Core import ImageManager

from .enhancement_nodes import Brightness, ColorBalance, Contrast, Sharpness
from .graph_abc import Edge, Node
from .image_nodes import ImageNode
from .inspect_nodes import HistogramNode, PreviewNode

logger = logging.getLogger("GUI.Editor")


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
                    dpg.add_menu_item(label="Preview", callback=self.add_preview_node)
                with dpg.menu(label="Enhance"):
                    dpg.add_menu_item(
                        label="Color Balance", callback=self.add_color_balance_node
                    )
                    dpg.add_menu_item(label="Contrast", callback=self.add_contrast_node)
                    dpg.add_menu_item(
                        label="Brightness", callback=self.add_brightness_node
                    )
                    dpg.add_menu_item(
                        label="Sharpness", callback=self.add_sharpness_node
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
        node = HistogramNode(
            label="Histogram", parent=self.node_editor, update_hook=self.evaluate
        )
        self.add_node(node)

    def add_preview_node(self):
        node = PreviewNode(
            label="Preview", parent=self.node_editor, update_hook=self.evaluate
        )
        self.add_node(node)

    def add_image_node(self):
        node = ImageNode(
            label="Image",
            parent=self.node_editor,
            image=self.image_manager.load(0),
            update_hook=self.evaluate,
        )
        self.add_node(node)

    def add_color_balance_node(self):
        node = ColorBalance(parent=self.node_editor, update_hook=self.evaluate)
        self.add_node(node)

    def add_contrast_node(self):
        node = Contrast(parent=self.node_editor, update_hook=self.evaluate)
        self.add_node(node)

    def add_brightness_node(self):
        node = Brightness(parent=self.node_editor, update_hook=self.evaluate)
        self.add_node(node)

    def add_sharpness_node(self):
        node = Sharpness(parent=self.node_editor, update_hook=self.evaluate)
        self.add_node(node)

    def topological_sort(self):
        """
        Get a list of nodes to process in the correct order.
        (A will not be before B if the output of B is required for A)
        """
        # kahn's algo: https://en.wikipedia.org/wiki/Topological_sorting
        sorted_list = []

        in_degree = defaultdict(int)
        for node in self.adjacency_list:
            for neighbour in self.adjacency_list[node]:
                in_degree[neighbour] += 1

        queue = [node for node in self.adjacency_list if in_degree[node] == 0]
        dropped = set()

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
        logger.debug(f"Execution order: {sorted_list}")

        if len(sorted_list) + len(dropped) != len(self.adjacency_list):
            logger.error("There is a cycle in your graph!!!")
            return []
        else:
            return sorted_list

    def evaluate(self):
        # TODO: parallelism???? Set up a process pool of some sort and greedily consume items from the sorted_node_list
        sorted_node_list = self.topological_sort()
        for node in sorted_node_list:
            node.process()
