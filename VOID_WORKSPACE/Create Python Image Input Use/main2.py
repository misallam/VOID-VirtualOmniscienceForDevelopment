# script2.py
import numpy as np
from icecream import ic

def extract_image_matrix(image):
    # Your image processing code here
    matrix = np.array([[9, 8, 7], [6, 5, 4], [3, 2, 1]])
    ic(matrix)

# Load image from file
image = None  # Load image here
extract_image_matrix(image)