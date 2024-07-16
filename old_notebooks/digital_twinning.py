from collections import defaultdict
# from lxml import etree
import json
import copy
import numpy as np
import requests
import shapely
import trimesh as tm 
import os
import glob
import zipfile
import pyvista as pv
import csv
# from ladybug.sunpath import Sunpath



# general support functions

def tri_to_pv(tri_mesh):
    """translate a trimesh to pyvista for visualisation purposes

    Args:
    tri_mesh (Trimesh.trimesh): the mesh that is to be visualized

    Returns:
    pv_mesh (pyvista mesh): the mesh, translated to the pyvista format
    """
    faces = np.pad(tri_mesh.faces, ((0, 0),(1,0)), 'constant', constant_values=3)
    pv_mesh = pv.PolyData(tri_mesh.vertices, faces)
    return pv_mesh

def save_to_clean_csv(lattice, final_dir):
    """remove empty lines in beginning of CSV file that disrupt the readability


    Args:
    temporary_dir: 
    final_dir: 
    Returns:
    """
    
    
    l = len(final_dir)
    temporary_dir = final_dir[:l-4] + '_temp.csv'

    csv_path = os.path.relpath(temporary_dir)
    lattice.to_csv(csv_path)

    index = 0
    with open(temporary_dir) as input, open(final_dir, 'w', newline='') as output:

        writer = csv.writer(output)
        for row in csv.reader(input):
            index +=1
            if index > 8: 
                writer.writerow(row)
            else: 
                if any(field.strip() for field in row):
                    writer.writerow(row)
    os.remove(temporary_dir)


# 3D BAG specific functions

# def etree_to_dict(gml_path):
#     """
#     read gml or xml files and save them to a python dictionary
#     #copied from https://stackoverflow.com/a/10076823

#     Args:
#     gml_path (string): location of the gml/xml file

#     Returns:
#     d (dict): json formatted dictionary

#     """
#     diagram = etree.parse(gml_path)
#     t = diagram.getroot()

#     d = {t.tag: {} if t.attrib else None}
#     children = list(t)
#     if children:
#         dd = defaultdict(list)
#         for dc in map(etree_to_dict, children):
#             for k, v in dc.items():
#                 dd[k].append(v)
#         d = {t.tag: {k: v[0] if len(v) == 1 else v
#                      for k, v in dd.items()}}
#     if t.attrib:
#         d[t.tag].update(('@' + k, v)
#                         for k, v in t.attrib.items())
#     if t.text:
#         text = t.text.strip()
#         if children or t.attrib:
#             if text:
#               d[t.tag]['#text'] = text
#         else:
#             d[t.tag] = text
#     return d

def read_json_dict(json_file_path):
    """ 
    Read json dictionaries, and extract specific information (tile id and coordinates of the boundaries). This function is explicitely only useful for reading the json dictionary from the 3D BAG. 
    Args: 
    json_file_path (string): the location of the JSON file 

    Returns: 
    new_tiles_dict (dict): a simplified dictionary with 5 columns("tile_id", "x1", "y1", "x2", "y2")
    """
    # Opening JSON file
    new_tiles_dict = [["tile_id", "x1", "y1", "x2", "y2"]]
    with open(json_file_path) as json_file:
        data = json.load(json_file)
        # retrieve the valuable data out of dictionary
        tiles = (data["{http://www.opengis.net/wfs}FeatureCollection"]["{http://www.opengis.net/gml}featureMembers"]["{bag3d_v2}bag_tiles_3k"])
        for i in tiles:
            tile = []
            tile.append(i['{bag3d_v2}tile_id'])
            tile.extend(i["{http://www.opengis.net/gml}boundedBy"]["{http://www.opengis.net/gml}Envelope"]['{http://www.opengis.net/gml}lowerCorner'].split())
            tile.extend(i["{http://www.opengis.net/gml}boundedBy"]["{http://www.opengis.net/gml}Envelope"]["{http://www.opengis.net/gml}upperCorner"].split())
            new_tiles_dict.append(tile)
    return new_tiles_dict

def download_3DBAG_gpkg(tile_list):

    """For each needed tile, download the corresponding 3d geopackage 

    Args: 
    tile_list (list): list of all tiles that are to be downloaded
    """
    for tile in tile_list:
        url = "https://data.3dbag.nl/gpkg/v21031_7425c21b/3dbag_v21031_7425c21b_" +str(tile) +str(".gpkg")
        r = requests.get(url, allow_redirects=True)
        file_name = '../data/QGIS_data/tile_' +str(tile) +str(".gpkg")
        with open(file_name, 'wb') as f:
            f.write(r.content)

def download_3DBAG_obj_zip(tile_list):
    """ For each needed tile, download the corresponding 3d obj file 
    Args: 
    tile_list (list): list of all tiles that are to be downloaded
    """
    for tile in tile_list:
        url = "https://data.3dbag.nl/obj/v21031_7425c21b/3dbag_v21031_7425c21b_" +str(tile) +str(".zip")
        r = requests.get(url, allow_redirects=True)
        file_name = '../data/tile_' +str(tile) +".zip"
        with open(file_name, 'wb') as f:
            f.write(r.content)

def unpack_objs(download_tiles, dir_base, dir_new):
    """
    extract the OBJ files from multiple 3D BAG zip files
    
    Args: 
    download_tiles (list): a list with all tiles that are to be downloaded
    dir_base (string)= location of all zip-files
    dir_new (string): location of all extracted OBJ files

    """

    file_names = []
    for tile in download_tiles: 
        end_obj = "lod22_3d_" +str(tile) +".obj"

        # based on https://stackoverflow.com/a/56229328
        for arc_name in glob.iglob(os.path.join(dir_base, "*.zip")):
            arc_dir_name = os.path.splitext(os.path.basename(arc_name))[0]
            zf = zipfile.ZipFile(arc_name)
            for file in zf.namelist():
                if file.endswith(end_obj):
                    file_names.append(file)
                    zf.extract(file, dir_new)
            zf.close()

        # remove all .zip files
        zip_file = '../data/tile_' +str(tile) +".zip"
        os.remove(zip_file)


# functions for generating meshes

def area_to_3d_obj(input_coords, height):
    """
    function to create a 3d OBJ mesh out of a list of points by extruding them in the Z-direction. the initial coordinates are being set to Z=0

    Args: 
    input_coords (list): all coordinates (2D) 
    height (float): 

    returns: 
    b_box_obj (Trimesh.trimesh): an extruded OBJ of the input coordinates
    """
    
    b_box_polygon = shapely.geometry.Polygon(input_coords)
    b_box_mesh = tm.creation.extrude_polygon(b_box_polygon, height, transform=None)
    b_box_obj = tm.exchange.obj.export_obj(b_box_mesh)
    return b_box_obj

def generate_vertices(in_coor_array, height):
    """ Extrude input coordinates to a set of 3d vertices (this function is deprecated and replaced by .... function)

    Args:
    in_coor_array (array): the mesh that describes the bounds
    height (float): the wished for extrusion height
    
    Returns: a list with all vertex locations in 3 dimensions, in the OBJ format
    """
    # def vertex_to_obj(coordinates):
    #     return " ".join(['v'] + ["%.2f" % i for i in coordinates])
    
    vert_count = len(in_coor_array)
    z = [0, height]
    vertices_obj = ['g']
    for value in z:
    # translate input coordinates to 3d vertices for generating an obj file
        base_vertices = np.c_[in_coor_array, [value]*vert_count]
        for coordinate in base_vertices:
            x = " ".join(['v'] + ["%.2f" % i for i in coordinate])
            vertices_obj.append(x)
    return vertices_obj
 
def generate_faces(vert_count): 
    """
    Generate vertical face elements for the extrusion as triangles

    Args:
    vert_count (int): amount of vertices that define the OBJ

    Returns:
    faces_obj (list): list with all faces of an extruded object, in the OBJ format
    """
    faces_obj = ['g']
    index = 0

    while vert_count > index:
        index +=1
        vertices = [[[index+ vert_count, 1, index], [index + vert_count, index+1, index]], [[1 + vert_count, 1, vert_count + index], [index + vert_count + 1, index + 1, index + vert_count]]]
        for triangle_type in vertices: 
        # if the vertex is the last one in the list, generate the face with the first vertex on the list
            if vert_count == (index): 
                x = " ".join(['f'] + ["%i" % i for i in (triangle_type[0])])
                faces_obj.append(x)
            # if not, generate a face with the next vertex on the list
            else: 
                x = " ".join(['f'] + ["%i" % i for i in (triangle_type[1])])
                faces_obj.append(x)
    return faces_obj


# functions for selecting and filtering

def buffer(b_box, scalar):
    # TODO: Add the docstrings

    # add a buffer margin
    b_box_scalex = (abs(b_box[0] - b_box[2]))*scalar
    b_box_scaley = (abs(b_box[1] - b_box[3]))*scalar

    #retrieve the scaled bounding box locations and save them as the b_box list
    b_box[0]= b_box[0] - b_box_scalex
    b_box[1]= b_box[1] - b_box_scaley
    b_box[2]= b_box[2] + b_box_scalex
    b_box[3]= b_box[3] + b_box_scaley
    return b_box

def overlap(boundary, input_locations): 
    # TODO: Add the docstrings

    # open the csv with all possible tile numbers and locations (coordinates)
    # input_locations.set_index('tile_id', inplace=True)

    #check whether a tile has overlap with the bounding box
    input_locations["x_bmin_tmax"] =  boundary[0] < input_locations["x2"]
    input_locations["x_bmax_tmin"] =  input_locations["x1"] < boundary[2]
    input_locations["y_bmin_tmax"] =  boundary[1] < input_locations["y2"]
    input_locations["y_bmax_tmin"] =  input_locations["y1"] < boundary[3]

    condition_matrix = input_locations[["x_bmin_tmax","x_bmax_tmin","y_bmin_tmax","y_bmax_tmin"]].to_numpy()
    indices = (condition_matrix.sum(axis=1) == 4)
    tile_ids = np.argwhere(indices)
    download_tiles = (tile_ids + 1).flatten().tolist()
    return download_tiles

def join_objs(dir_name_base):
    # TODO: Add the docstrings

    all_scenes = []

    # load all files
    for arc_name in glob.iglob(os.path.join(dir_name_base, "*.obj")):
        mesh = tm.load_mesh(arc_name)
        all_scenes.append(mesh)

    #from all scenes, append the vertices to one array (all_v) and the faces to another (all_f)
    all_v = []
    all_f = []
    for scene in all_scenes:
        for _, mesh in scene.geometry.items():
            all_v.append(np.array(mesh.vertices))
            all_f.append(np.array(mesh.faces))

    # as all vertices are now in one list and the faces are generated based on the index of each vertex, these values should be adjusted to the new vertex indices. 
    adjusted_all_f = []
    vcount = 0
    for vs, fs in zip(all_v, all_f):
        fs += vcount
        adjusted_all_f.append(fs)
        vcount += vs.shape[0]

    #concatenate all faces and all vertices into an array
    v_array = np.concatenate(all_v)
    f_array = np.concatenate(adjusted_all_f)

    # translate the vertices and faces to an .obj format
    combined_mesh = tm.Trimesh(v_array, f_array)
    context_mesh = tm.exchange.obj.export_obj(combined_mesh)
    return context_mesh

def vertex_intersection(bound_mesh, content_mesh):
    """[summary]

    Args:
        bound_mesh (Trimesh): the mesh that describes the bounds
        content_mesh (Trimesh): the content mesh

    Returns:
        Trimesh: the trimmed mesh
    """
    # check which one of the vertices of the content_mesh is inside the bound_mesh
    v_inside = bound_mesh.contains(content_mesh.vertices)
    # check which one of the faces of the content_mesh correspond to the vertices of it that fall inside the bound_mesh
    f_inside = v_inside[content_mesh.faces].all(axis=1)
    # making a deep copy of the content_mesh
    inside_mesh = copy.deepcopy(content_mesh)
    # removing the external vertices
    inside_mesh.update_vertices(v_inside)
    # removing the external faces
    inside_mesh.update_faces(f_inside)
    return inside_mesh

def vertex_difference(bound_mesh, content_mesh):
    """[summary]

    Args:
        bound_mesh (Trimesh): the mesh that describes the bounds
        content_mesh (Trimesh): the content mesh

    Returns:
        Trimesh: the trimmed mesh
    """
    # check which one of the vertices of the content_mesh is inside the bound_mesh
    v_inside = bound_mesh.contains(content_mesh.vertices)
    # find the vertices that fall outside
    v_outside = (1 - v_inside).astype(bool)
    # check which one of the faces of the content_mesh correspond to the vertices of it that fall outside the bound_mesh
    f_outside = v_outside[content_mesh.faces].all(axis=1)
    # making a deep copy of the content_mesh
    outside_mesh = copy.deepcopy(content_mesh)
    # removing the internal vertices
    outside_mesh.update_vertices(v_outside)
    # removing the internal faces
    outside_mesh.update_faces(f_outside)
    return outside_mesh

# def sun_positions():
#     # TODO: Add the docstrings
#     # initiate sunpath
#     sp = Sunpath(longitude=4.3571, latitude=52.0116)

#     # defining sun hours
#     sun_vectors = []
#     day_multiples = 30
#     for d in range(365):
#         if d % day_multiples==0:
#             for h in range(24):
#                 i = d*24 + h
#                 # compute the sun object
#                 sun = sp.calculate_sun_from_hoy(i)
#                 # extract the sun vector
#                 sun_vector = sun.sun_vector.to_array()
#                 # Removing the sun vectors under the horizon 
#                 if sun_vector[2] > 0.0:
#                     sun_vectors.append(sun_vector)

#     sun_vectors = np.array(sun_vectors)
    
#     return sun_vectors

def sky_positions():
    #Create a sphere to put points on that represent the sky 
    sphere_mesh = tm.creation.icosphere(subdivisions=2, radius= 300.0, color=None)
    sphere_vectors = np.copy(sphere_mesh.vertices)
    sky_vectors = []
    for v in sphere_vectors:
        if v[2] > 0.0:
            sky_vectors.append(v)


    sky_vectors = np.array(sky_vectors)

    return sky_vectors