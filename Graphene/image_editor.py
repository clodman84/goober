import itertools
import logging
from collections import defaultdict, deque
from pathlib import Path
from line_profiler import profile

import dearpygui.dearpygui as dpg

import Graphene.Nodes as Nodes
from Graphene.Core import ImageManager
from Graphene.Nodes.graph_abc import Edge

logger = logging.getLogger("GUI.Editor")


class EditingWindow:
    def __init__(self, source: list[Path]) -> None:
        self.image_manager = ImageManager.from_file_list(
            source, (600, 600), thumbnail_dimensions=(200, 200)
        )
        self.node_lookup_by_attribute_id = {}
        self.edge_lookup_by_edge_id = {}
        self.adjacency_list: dict[Nodes.Node, list[Nodes.Node]] = {}

        with dpg.window(label="Image Editor", width=500, height=500):
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(
                        label="Import Image",
                        callback=self.add_image_node,
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text("Add an image source node from your file list.")

                with dpg.menu(label="Adjustments"):
                    dpg.add_menu_item(
                        label="Brightness", callback=self.add_brightness_node
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(
                            "Adjust overall lightness or darkness of the image."
                        )

                    dpg.add_menu_item(label="Contrast", callback=self.add_contrast_node)
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text("Increase or decrease contrast between tones.")

                    dpg.add_menu_item(
                        label="Saturation", callback=self.add_saturation_node
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text("Control colour intensity or vividness.")

                    dpg.add_menu_item(
                        label="Colour Balance", callback=self.add_colour_balance_node
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(
                            "Adjust colour in shadows, midtones and highlights independently."
                        )

                    dpg.add_menu_item(label="Levels", callback=self.add_levels_node)
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(
                            "Make dark things darker or light things lighter or both."
                        )

                # with dpg.menu(label="Filters"):
                #     dpg.add_menu_item(
                #         label="Sharpness", callback=self.add_sharpness_node
                #     )
                #     with dpg.tooltip(dpg.last_item()):
                #         dpg.add_text("Enhance fine details and edges.")

                with dpg.menu(label="Channel Ops"):
                    dpg.add_menu_item(
                        label="RGB Splitter", callback=self.add_rgb_splitter_node
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text("Split image into red, green, and blue channels.")

                    dpg.add_menu_item(
                        label="Tone Splitter", callback=self.add_smh_splitter_node
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(
                            "Split image into shadows, midtones, and highlights."
                        )

                    dpg.add_menu_item(
                        label="Merge Channels", callback=self.add_merge_node
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(
                            "Merge separate channel outputs back into one image."
                        )

                with dpg.menu(label="View"):
                    dpg.add_menu_item(label="Preview", callback=self.add_preview_node)
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text("Render and view the final processed image.")

                    dpg.add_menu_item(
                        label="Histogram", callback=self.add_histogram_node
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(
                            "Display tonal distribution of the connected image."
                        )

                with dpg.menu(label="Graph"):
                    dpg.add_menu_item(
                        label="Evaluate Graph",
                        callback=lambda: self.evaluate(is_final=True),
                    )
                    with dpg.tooltip(dpg.last_item()):
                        dpg.add_text(
                            "Run the entire node graph and update all outputs."
                        )

            with dpg.node_editor(
                callback=self.link, delink_callback=self.delink, minimap=True
            ) as self.node_editor:
                pass

    def link(self, sender, app_data):
        id = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
        logger.debug(self.node_lookup_by_attribute_id)

        input: Nodes.Node = self.node_lookup_by_attribute_id[app_data[0]]
        output: Nodes.Node = self.node_lookup_by_attribute_id[app_data[1]]

        edge = Nodes.Edge(id, None, input, output, app_data[0], app_data[1])
        self.edge_lookup_by_edge_id[id] = edge
        self.adjacency_list[input].append(output)
        edge.connect()

    def delink(self, sender, app_data):
        edge: Edge = self.edge_lookup_by_edge_id[app_data]
        edge.disconnect()
        self.adjacency_list[edge.input].remove(edge.output)
        self.edge_lookup_by_edge_id.pop(edge.id)

    def delete_node(self, node):
        incoming = [e for edges in node.input_attributes.values() for e in edges]
        outgoing = [e for edges in node.output_attributes.values() for e in edges]

        # If exactly one input and one output, remember the nodes for reconnection
        reconnect = None
        if len(incoming) == 1 and len(outgoing) == 1:
            a = incoming[0].input  # Upstream node
            c = outgoing[0].output  # Downstream node
            reconnect = (a, c)

        # Delink all connected edges
        for edge in incoming + outgoing:
            edge_id = edge.id
            if edge_id in self.edge_lookup_by_edge_id:
                self.delink(self.node_editor, edge_id)
                self.edge_lookup_by_edge_id.pop(edge_id, None)

        # Reconnect A -> C if valid
        if reconnect:
            a, c = reconnect
            if a.output_attributes and c.input_attributes and a is not c:
                self.link(
                    self.node_editor,
                    (next(iter(a.output_attributes)), next(iter(c.input_attributes))),
                )

        self.adjacency_list.pop(node, None)
        for adj in self.adjacency_list.values():
            if node in adj:
                adj.remove(node)

        for attr_id in itertools.chain(node.input_attributes, node.output_attributes):
            self.node_lookup_by_attribute_id.pop(attr_id, None)

    def add_node(self, node: Nodes.Node):
        for attribute in itertools.chain(node.input_attributes, node.output_attributes):
            self.node_lookup_by_attribute_id[attribute] = node
        node.delete_hook = lambda: self.delete_node(node)
        self.adjacency_list[node] = []

    def add_rgb_splitter_node(self):
        node = Nodes.RGBSplitter(
            label="RGB Splitter", parent=self.node_editor, update_hook=self.evaluate
        )
        self.add_node(node)

    def add_merge_node(self):
        node = Nodes.Merge(
            label="Merge", parent=self.node_editor, update_hook=self.evaluate
        )
        self.add_node(node)

    def add_smh_splitter_node(self):
        node = Nodes.SMHSplitter(
            label="Tone Splitter", parent=self.node_editor, update_hook=self.evaluate
        )
        self.add_node(node)

    def add_histogram_node(self):
        node = Nodes.HistogramNode(
            label="Histogram", parent=self.node_editor, update_hook=self.evaluate
        )
        self.add_node(node)

    def add_preview_node(self):
        node = Nodes.PreviewNode(
            label="Preview", parent=self.node_editor, update_hook=self.evaluate
        )
        self.add_node(node)

    def add_image_node(self):
        node = Nodes.ImageNode(
            label="Image",
            parent=self.node_editor,
            image=self.image_manager.load(0),
            update_hook=self.evaluate,
        )
        self.add_node(node)

    def add_saturation_node(self):
        node = Nodes.Saturation(parent=self.node_editor, update_hook=self.evaluate)
        self.add_node(node)

    def add_contrast_node(self):
        node = Nodes.Contrast(parent=self.node_editor, update_hook=self.evaluate)
        self.add_node(node)

    def add_brightness_node(self):
        node = Nodes.Brightness(parent=self.node_editor, update_hook=self.evaluate)
        self.add_node(node)

    def add_sharpness_node(self):
        node = Nodes.Sharpness(parent=self.node_editor, update_hook=self.evaluate)
        self.add_node(node)

    def add_colour_balance_node(self):
        node = Nodes.ColourBalance(
            label="Colour Balance",
            parent=self.node_editor,
            update_hook=self.evaluate,
        )
        self.add_node(node)

    def add_levels_node(self):
        node = Nodes.Levels(
            label="Levels", parent=self.node_editor, update_hook=self.evaluate
        )
        self.add_node(node)

    def get_visible_nodes(self):
        """
        Get a list of nodes that are not eventually connected to an InspectNode
        """
        inspect_nodes = [
            node for node in self.adjacency_list if isinstance(node, Nodes.InspectNode)
        ]
        visible_nodes = set(inspect_nodes)
        q = deque(inspect_nodes)
        while q:
            node = q.popleft()
            for edge_list in node.input_attributes.values():
                for edge in list(edge_list):  # copy to avoid mutation problems
                    parent = edge.input
                    if parent not in visible_nodes:
                        visible_nodes.add(parent)
                        q.append(parent)
        return visible_nodes

    def topological_sort(self):
        """
        Get a list of nodes to process in the correct order.
        (A will not be before B if the output of B is required for A)
        """
        # just kahn's algo: https://en.wikipedia.org/wiki/Topological_sorting
        in_degree = defaultdict(int)
        for node in self.adjacency_list:
            for neighbour in self.adjacency_list[node]:
                in_degree[neighbour] += 1

        queue = [node for node in self.adjacency_list if in_degree[node] == 0]
        dropped = [node for node in self.adjacency_list if node.state == 0]
        sorted_list = []

        while queue:
            node = queue.pop()
            if node.state == 1:
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

    # TODO: this bit can be cleaned up
    @profile
    def evaluate(self, is_final=False):
        if is_final:
            # activate all image nodes
            logger.debug(f"Activated all ImageNodes, is_final: {is_final}")
            for node in self.adjacency_list.keys():
                if isinstance(node, Nodes.ImageNode):
                    node.activate()

        visible_nodes = self.get_visible_nodes()
        sorted_node_list = self.topological_sort()

        logger.debug(
            f"Sorted node list: {sorted_node_list}, Visible Nodes: {visible_nodes}"
        )
        for node in sorted_node_list:
            if node in visible_nodes:
                logger.debug(f"Processed Node {node}")
                node.process(is_final=is_final)
                node.state = 0
                logger.debug(f"{node} state changed to 0")
