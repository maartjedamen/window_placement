from flask import Flask
import ghhops_server as hs
import rhino3dm


# register hops app as middleware
app = Flask(__name__)
hops = hs.Hops(app)

@hops.component(
    "/pointat",
    name="PointAt",
    description="Get point along curve",
    icon="examples/pointat.png",
    inputs=[
        hs.HopsCurve("Curve", "C", "Curve to evaluate"),
        hs.HopsNumber("t", "t", "Parameter on Curve to evaluate"),
        
    ],
    outputs=[
        hs.HopsPoint("P", "P", "Point on curve at t")
    ]
)
def pointat(curve, t):
    # return curve.PointAt(t)
    return curve.PointAt(t)


@hops.component(
        "/json",
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

def import_json(filepath): 
    # load input coordinates from a geojson file
    with open("filepath") as json_file:
        data = json.load(json_file)
        # retrieve the valuable data out of dictionary
        # tiles = (data["features"][0]["geometry"]["coordinates"])
        tiles = (data["features"])

    coords = []
    for n in range(len(tiles)):
        features = (data["features"][n]["geometry"]["coordinates"])
        coords.append(features)
    return coords

if __name__ == "__main__":
    app.run()



# @hops.component(
#     "/Gen",
#     name="GenerateSpheresFromImage",
#     nickname="GSI",
#     description="Generate spheres based on image RGB values",
#     inputs=[
#         hs.HopsString("ImagePath", "Image", "Path to the image file")
#     ],
#     outputs=[
#         hs.HopsBrep("Spheres", "S", "List of spheres generated"),
#         hs.HopsString("Log", "L", "Log or error message")
#     ]
# )


# def generate_spheres_from_image(image_path: str) -> (list, str):
#     try:
#         image = Image.open(image_path)
#     except Exception as e:
#         return [], f"Failed to load image. Error: {e}"
        
#     # Use PIL to open and process the image
#     try:
#         image = Image.open(image_path)
#     except Exception as e:
#         return [], f"Failed to load image. Error: {e}"

#     width, height = image.size

#     try:
#         pixels = image.load()
#     except Exception as e:
#         return [], f"Failed to load pixels. Error: {e}"

#     spheres = []

#     # Use the double for loop to create geometries
#     for i in range(height):
#         for j in range(width):
#             if i % 2 == 0 and j % 2 == 0:
#                 pixel_color = pixels[j, i]


#                 r, g, b, _ = pixel_color


#                 center = rg.Point3d(i, height - 1 - j, 0)
#                 radius = r / 150.0

#                 # Explicitly check for zero or negative radius
#                 if radius <= 0.0:
#                     return [], f"Invalid radius ({radius}) at center: {center}. Pixel RGB: ({r},{g},{b})"

#                 sphere = rg.Sphere(center, radius)

#                 if not sphere.IsValid:
#                     return [], f"Sphere creation failed at center: {center}. Pixel RGB: ({r},{g},{b}), Radius: {radius}"
#                 else:
#                     spheres.append(sphere.ToBrep())  # Convert to Brep for output

#     return spheres, "Success"
#     # Use PIL to open and process the image
