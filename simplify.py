import svgpathtools as spt


def check_points(paths, start_pnts, end_pnts):
    for i, a_path in enumerate(paths):
        if i != start_pnts[a_path.start]:
            raise
        if i != end_pnts[a_path.end]:
            raise


def add_end_points(a_path, i, start_pnts, end_pnts):
    if a_path.start in start_pnts:
        raise
    if a_path.end in end_pnts:
        raise
    start_pnts[a_path.start] = i
    end_pnts[a_path.end] = i


def remove_old_endpoints(a_path, start_pnts, end_pnts, ):
    del start_pnts[a_path.start]
    del end_pnts[a_path.end]


def combine_paths(path_1, path_2):
    if path_1.end == path_2.start:
        return spt.Path(*path_1._segments, *path_2._segments)
    elif path_1.start == path_2.start:
        return spt.Path(*path_1.reversed()._segments, *path_2._segments)
    elif path_1.end == path_2.end:
        return spt.Path(*path_1._segments, *path_2.reversed()._segments)
    elif path_1.start == path_2.end:
        return spt.Path(*path_1.reversed()._segments, *path_2.reversed()._segments)
    else:
        raise


def get_index(a_path, start_points, end_points):
    if a_path.start in start_points:
        return start_points[a_path.start]
    elif a_path.end in start_points:
        return start_points[a_path.end]
    elif a_path.start in end_points:
        return end_points[a_path.start]
    elif a_path.end in end_points:
        return end_points[a_path.end]
    else:
        return None


def simplify_paths(paths):
    start_points = dict()
    end_points = dict()
    i = 0
    new_paths = []
    for a_path in paths:
        if not isinstance(a_path, spt.Path):
            a_path = spt.Path(a_path)
        index = get_index(a_path, start_points, end_points)
        if index is None:
            add_end_points(a_path, i, start_points, end_points)
            new_paths.append(a_path)
            i += 1
            continue
        old_index = None
        while index is not None:
            old_path = new_paths[index]
            remove_old_endpoints(old_path, start_points, end_points)
            new_paths[index] = []
            new_path = combine_paths(a_path, old_path)
            old_index = index
            index = get_index(new_path, start_points, end_points)
            a_path = new_path
        add_end_points(new_path, old_index, start_points, end_points)
        new_paths[old_index] = new_path

    paths = []
    for a_path in new_paths:
        if len(a_path) > 0:
            paths.append(a_path)
    return paths


def get_paths_from_doc(file_name, file_dir):
    paths = []
    doc = spt.document.Document(file_dir + file_name + ".svg")
    list_of_paths = doc.paths()

    for a_path in list_of_paths:
        if len(a_path) > 0:
            paths.extend(a_path)
    return paths


file_input_dir = "outputs\\raw_svg\\"
file_output_dir = "outputs\\simplified\\"
file_names = ["floyd_stippling_founders_0", "floyd_stippling_founders_1", "floyd_stippling_founders_2"]
for file_name in file_names:
    paths = get_paths_from_doc(file_name, file_input_dir)
    paths = simplify_paths(paths)
    spt.paths2svg.wsvg(paths, filename=file_output_dir + file_name + ".svg")