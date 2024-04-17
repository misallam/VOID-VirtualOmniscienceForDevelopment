# script1.py
import numpy as np
from icecream import ic

def extract_image_matrix(image):
    # Your image processing code here
    matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    ic(matrix)

# Load image from file
image = None  # Load image here
extract_image_matrix(image)