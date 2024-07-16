from flask import Flask
import ghhops_server as hs
import rhino3dm
import json
import flatgeobuf as fgb

# register hops app as middleware
app = Flask(__name__)
hops = hs.Hops(app)

@hops.component(
    "/pointat",
    name="PointAt",
    description="Get point along curve",
    # icon="examples/pointat.png",
    inputs=[
        hs.HopsCurve("Curve", "C", "Curve to evaluate"),
        hs.HopsNumber("t", "t", "Parameter on Curve to evaluate"),
    ],
    outputs=[
        hs.HopsPoint("P", "P", "Point on curve at t")
    ]
)

def pointat(curve, t):
    return curve.PointAt(t)


"-----------------------------------------------------------"

@hops.component(
        "/geojsonfile",
        name="importjson",
        nickname="json",
        description="import GIS point based information from a JSON file to grasshopper",
        inputs=[
            hs.HopsString("Filepath", "JSON", "Path to JSON file"),
        ],
        outputs=[
            hs.HopsPoint("P", "P", "point list from GIS")
        ]
)

def geojsonfile(filepath):
    with open(filepath) as json_file:
        data = json.load(json_file)
        # retrieve the valuable data out of dictionary
        # tiles = (data["features"][0]["geometry"]["coordinates"])
    #     tiles = (data["features"])

    # coords = []

    # # for n in range(20):
    # for n in range(len(tiles)):
    #     features = (data["features"][n]["geometry"]["coordinates"])
    #     coords.append(features)
    return(data)


# def geojsonfile(filepath): 
    # coords = []
    # # load input coordinates from a geojson file
    # with open(filepath) as json_file:
    #     # with open("data/tile_index.fgb", "rb") as f:
    #     reader = fgb.Reader(json_file)
    #     # for index, item in enumerate(items):
    #     # print(index, item)
    #     for index, feature in enumerate(reader):
    #     # print(feature)
    #         coords.append(feature["features"][index]["geometry"]["coordinates"])
    #         # clean_tiles_dict.append(feature["properties"]["tile_id"])
    
    
    #     # data = json.load(json_file)
    #     # retrieve the valuable data out of dictionary
    #     # tiles = (data["features"][0]["geometry"]["coordinates"])
    #     # tiles = (data["features"])


    # # for n in range(len(tiles)):
    # #     features = (data["features"][n]["geometry"]["coordinates"])

    #     # json.dumps(features)
    
    # # coords = json.dumps(coords)
    
    # return coords



# @hops.component(
#     "importOSM", 
#     name="importOSM", 
#     nickname="OSM",
#     description="import OSM information based on a bounding box",
#     inputs=[
#         hs.HopsPoint("corner1", "p1", 'first corner bounding box')
#         hs.HopsPoint("corner2", "p2", 'first corner bounding box')
#         hs.HopsPoint("corner3", "p3", 'first corner bounding box')
#         hs.HopsPoint("corner4", "p4", 'first corner bounding box')
#     ]
# )


if __name__ == "__main__":
    app.run()

