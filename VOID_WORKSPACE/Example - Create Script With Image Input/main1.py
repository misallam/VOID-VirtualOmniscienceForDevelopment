import cv2
import numpy as np

def extract_image_matrix(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None

    image_matrix = np.array(image)
    return image_matrix

image_path = "path/to/your/image.png"
result = extract_image_matrix(image_path)
if result is not None:
    print(result)
