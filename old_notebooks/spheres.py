def generate_spheres_from_image(image_path: str) -> (list, str):

    # Use PIL to open and process the image
    try:
        image = Image.open(image_path)
    except Exception as e:
        return [], f"Failed to load image. Error: {e}"

    width, height = image.size

    try:
        pixels = image.load()
    except Exception as e:
        return [], f"Failed to load pixels. Error: {e}"

    spheres = []

    # Use the double for loop to create geometries
    for i in range(height):
        for j in range(width):
            if i % 2 == 0 and j % 2 == 0:
                pixel_color = pixels[j, i]


                r, g, b, _ = pixel_color


                center = rg.Point3d(i, height - 1 - j, 0)
                radius = r / 150.0

                # Explicitly check for zero or negative radius
                if radius <= 0.0:
                    return [], f"Invalid radius ({radius}) at center: {center}. Pixel RGB: ({r},{g},{b})"

                sphere = rg.Sphere(center, radius)

                if not sphere.IsValid:
                    return [], f"Sphere creation failed at center: {center}. Pixel RGB: ({r},{g},{b}), Radius: {radius}"
                else:
                    spheres.append(sphere.ToBrep())  # Convert to Brep for output

                # Skip the black pixels
                if r == 0 and g == 0 and b == 0:
                    continue  # Skip the current loop iteration


                # Skip pixels with red value below the threshold
                if r < MIN_RED_VALUE:
                    continue

                center = rg.Point3d(i, height - 1 - j, 0)
                radius = r / 150.0

                # If radius is still below the minimum threshold, assign a minimum radius
                if radius < MIN_RADIUS:
                    radius = MIN_RADIUS

                sphere = rg.Sphere(center, radius)
    return spheres, "Success"

