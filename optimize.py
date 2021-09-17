import glob
import numpy as np
import svgpathtools
import colorsys
import rtree
from collections import Counter


def generate_color(hue, saturation=1.0, value=1.0):
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    return 'rgb({},{},{})'.format(*[int(x * 255) for x in rgb])


def dist(p1, p2):
    return np.linalg.norm(p1 - p2, ord='inf')


def cost_of_route(path, origin=0. + 0j):
    # Cost from the origin to the start of the first path
    cost = dist(origin, path[0].start)
    # Cost between the end of each path and the start of the next
    cost += sum(
        dist(path[i].end, path[i + 1].start) for i in range(len(path) - 1)
    )
    # Cost to return back to the origin
    cost += dist(path[-1].end, origin)
    return cost


class PathGraph:
    # The origin is always at index 0.
    ORIGIN = 0

    def __init__(self, paths, origin=0. + 0j):
        """Constructs a PathGraph from the output of svgpathtools.svg2paths."""
        self.paths = paths
        # For any node i, endpoints[i] will be a pair containing that node's
        # start and end coordinates, respectively. For i==0 this represents
        # the origin.
        self.endpoints = [(origin, origin)]

        for path in paths:
            # For each path in the original list of paths,
            # create nodes for the path as well as its reverse.
            self.endpoints.append((path.start, path.end))
            self.endpoints.append((path.end, path.start))

    def get_path(self, i):
        """Returns the path corresponding to the node i."""
        index = (i - 1) // 2
        reverse = (i - 1) % 2
        path = self.paths[index]
        if reverse:
            return path.reversed()
        else:
            return path

    def cost(self, i, j):
        """Returns the distance between the end of path i
        and the start of path j."""
        return dist(self.endpoints[i][1], self.endpoints[j][0])

    def get_coordinates(self, i, end=False):
        """Returns the starting coordinates of node i as a pair,
        or the end coordinates iff end is True."""
        if end:
            endpoint = self.endpoints[i][1]
        else:
            endpoint = self.endpoints[i][0]
        return (endpoint.real, endpoint.imag)

    def iter_starts_with_index(self):
        """Returns a generator over (index, start coordinate) pairs,
        excluding the origin."""
        for i in range(1, len(self.endpoints)):
            yield i, self.get_coordinates(i)

    def get_disjoint(self, i):
        """For the node i, returns the index of the node associated with
        its path's opposite direction."""
        return ((i - 1) ^ 1) + 1

    def iter_disjunctions(self):
        """Returns a generator over 2-element lists of indexes which must
        be mutually exclusive in a solution (i.e. pairs of nodes which represent
        the same path in opposite directions.)"""
        for i in range(1, len(self.endpoints), 2):
            yield [i, self.get_disjoint(i)]

    def num_nodes(self):
        """Returns the number of nodes in the graph (including the origin.)"""
        return len(self.endpoints)


class PathIndex:
    def __init__(self, path_graph):
        self.idx = rtree.index.Index()
        self.path_graph = path_graph
        for index, coordinate in path_graph.iter_starts_with_index():
            self.idx.add(index, coordinate + coordinate)

    def get_nearest(self, coordinate):
        return next(self.idx.nearest(coordinate))

    def delete(self, index):
        coordinate = self.path_graph.get_coordinates(index)
        self.idx.delete(index, coordinate + coordinate)

    def delete_pair(self, index):
        self.delete(index)
        self.delete(self.path_graph.get_disjoint(index))


def greedy_walk(path_graph):
    path_index = PathIndex(path_graph)
    location = path_graph.get_coordinates(path_graph.ORIGIN)
    while True:
        try:
            next_point = path_index.get_nearest(location)
        except StopIteration:
            break
        location = path_graph.get_coordinates(next_point, True)
        path_index.delete_pair(next_point)
        yield next_point


def check_valid_solution(solution, graph):
    """Check that the solution is valid: every path is visited exactly once."""
    expected = Counter(
        i for (i, _) in graph.iter_starts_with_index()
        if i < graph.get_disjoint(i)
    )
    actual = Counter(
        min(i, graph.get_disjoint(i))
        for i in solution
    )

    difference = Counter(expected)
    difference.subtract(actual)
    difference = {k: v for k, v in difference.items() if v != 0}
    if difference:
        print('Solution is not valid!'
              'Difference in node counts (expected - actual): {}'.format(difference))
        return False
    return True


def get_route_from_solution(solution, graph):
    """Converts a solution (a list of node indices) into a list
    of paths suitable for rendering."""
    # As a guard against comparing invalid "solutions",
    # ensure that this solution is valid.
    assert check_valid_solution(solution, graph)
    return [graph.get_path(i) for i in solution]


input_directory = "outputs\\simplified\\"
output_directory = "outputs\\optimized\\"
file_names = glob.glob(input_directory + "*")
for a_file_path in file_names:
    if "floyd_stippling_founders" in a_file_path:
        a_file_name = a_file_path.split("\\")[-1]
        paths, _ = svgpathtools.svg2paths(a_file_path)
        path_graph = PathGraph(paths)
        greedy_solution = list(greedy_walk(path_graph))
        greedy_route = get_route_from_solution(greedy_solution, path_graph)
        svgpathtools.wsvg(greedy_route, filename=output_directory + a_file_name)