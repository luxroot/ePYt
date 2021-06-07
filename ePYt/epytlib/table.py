# Mappings from graph_node to memory
class Table:
    def __init__(self, graph_nodes, initial_memory):
        self.table = {}
        for graph_node in graph_nodes:
            self.table[graph_node] = initial_memory

    def __getitem__(self, item):
        return self.table[item]

    def __setitem__(self, key, value):
        self.table[key] = value

    def __str__(self):
        return '\n'.join(map(str, self.table.items()))

    def __repr__(self):
        return f"<Table{str(self)}>"
