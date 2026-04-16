# Contains all the functions for:
# 1. preprocessing for plate analysis
# 2. Identifying coordinates of top and bottom plates and edges. 
# 3. Pixel to diameter calibraitons


import cv2
import skimage as ski
from skimage import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import preprocessing as preproc


# Defaults:
DEFAULT_HLINE_PARAMS = {"threshold": 10,
                        "line_length": 20,
                        "range": 100,
                        "line_gap": 15}

def get_default_split_params(h: int) -> dict:
    """ Computes default image split boundaries for finding top and bottom plates.
    Parameters:
        h: int
            height of a the frame
    Returns: dict
        Dictionary containing parameters being used to sort top lines corresponding to the top plate and bottom plate
            - "top_cutoff": int Default = Height of image/2. 
                    This is a pixel value along the y axis somewhere below the top plate. Recommended: Height of image/2
            - "bottom_cutoff": int Default = Height of image/2+100. 
                    This is a pixel value along the y axis below the top_cutoff value, but above the bottom plate. Recommended: Height of image/2 + 100
        """
    return {"top_cutoff": int(h/2),
            "bottom_cutoff": int(h/2 + 60)}

# Functions
# Prepare image
def enhhance_contrast(frame: np.ndarray, crop_params: dict) -> np.ndarray:
    """ Takes a raw frame of the video and returns a cropped, blurred and sigmoid-corrected grayscale image

    Parameters:
    frame: np.ndarray
        This is the raw frame from cv2   

    crop_params: dict 
        Dictionary containing pixel coordinates for cropping the image. Coordinates should be chosen to leave empty space around the plates.
        top/bottom plate pair in question must be as close to centered as possible
        
        Expected Keys:
        - "top": int
            Pixel index at top of frame above top plate 
        - "bottom": int
            Pixel index at bottom of frame, below the length of the plate
        - "left" : int
            Pixel index at left of frame, leaving blank space around the plate
        - "right" : int
            Pixel index at right of frame, leaving blank space around the plate       
        
    Returs: np.ndarray 
        blurred, sigmoid corrected grayscale image for use with scikit image. """
    
    cropped = preproc.cropped_grayscale(frame = frame, crop_params = crop_params) # Crop
    blurred = ski.filters.gaussian(cropped, sigma = 0.5)    # Gaussian blur
    contrast_enhanced_img = ski.exposure.adjust_sigmoid(blurred, cutoff = 0.35, gain = 15) # Enhance contrast 

    return contrast_enhanced_img

def edge_binarize(frame: np.ndarray, sobel_mask_val: float = 0.6, morph_star_kernel_size: int = 10) -> np.ndarray:
    """ Takes a contrast enhanced frame and binarizes after finding edges of plates and other features via the sobel filter. 
    Returns the skeletonized image

    Parameters:
    frame: np.ndarray:
        A sigmoid-corrected contrast enhanced frame
        
    sobel_mask_val: float. Optional, default = 0.6
        The value used to define the mask cutoff between the max and mean intensities of the sobel edges.
        Used to filter out all unimportant edges and only keep dominant edges.
    
    morph_star_kernel_size: int. Optional, default = 10 
        The size of the star kernel used for morphology corrections
    
    Returns: np.ndarray
        Skeletonized image"""
    
    # Sobel filter
    sobeledge = ski.filters.sobel(frame)

    # Create mask for finding dominant edge lines
    smask = sobeledge < (sobeledge.max() - sobeledge.mean())*sobel_mask_val
    sobeledge[smask] = 1                    # amplify important lines
    sobeledge = ski.util.invert(sobeledge)  # Invert values to make edges white. 

    # otsu thresholding to make binary
    tvalue = ski.filters.threshold_otsu(sobeledge)          
    sobeledge = sobeledge > tvalue

    # morphological closing corrections
    k = ski.morphology.star(morph_star_kernel_size)         
    morph = ski.morphology.binary_closing(sobeledge, footprint = k)

    # Skeletonizing - turning edges to single pixel lines.  
    skeletonized = ski.morphology.skeletonize(morph)        
    return skeletonized

# Getting coordinates of top and bottom plates
def get_hough_lines(frame: np.ndarray, hline_params: dict = None, split_params: dict = None) -> tuple:
    """ Takes a skeletonized frame and finds and sorts  the hough lines around the top and bottom plates. 
    Returns a tuple of lists (top_lines, bottom_lines). Each line has format ((x0, y0), (x1, y1)), indicating line start and line end respectively. 
    top_lines are those that are visually in the top portion of the image around the top_plate, 
    and bottom_lines are those that are visually on the lower portion of the image, around the bottom plate

    Parameters:
    frame: np.ndarray
        A skeletonized frame
    
    hline_params: dict = None
        Optional
        Dictionary containing parameters being used for hough-line detection. 
        Expected keys are one or more of:
        - "threshold": int Default= 10
        - "line_length": int Default = 20
        - "range": int Default = 100
        - "line_gap": int Default = 15
            note: see scikit image documentation for hough-lines to understand what these inputs mean.

    split_params: dict = None
        Optional, but recommended
        Dictionary containing parameters being used to sort top lines corresponding to the top plate and bottom plate
        Expected keys are one or more of:
        - "top_cutoff": int Default = Height of image/2. 
                This is a pixel value along the y axis somewhere below the top plate. Recommended: Height of image/2
        - "bottom_cutoff": int Default = Height of image/2+60. 
                This is a pixel value along the y axis below the top_cutoff value, but above the bottom plate. Recommended: Height of image/2 + 60
    
    Returns: tuple
        (top_lines, bottom_lines). 
            Each item is a list of lines.
            Each line has format ((x0, y0), (x1, y1))"""
    
    # Setting defaults
    
    h,w = frame.shape
    default_split_params = get_default_split_params(h)
    
    # Updating parameters
    if hline_params is None:
        # No user provided dict, use defaults
        hline_params = DEFAULT_HLINE_PARAMS.copy()
    else: 
        # Update hline params to incorporate defaults and the user defined values
        temp_hline = DEFAULT_HLINE_PARAMS.copy() # Create defaults copy
        temp_hline.update(hline_params)
        hline_params = temp_hline

    if split_params is None:
        # No user provided dict, use defaults
        split_params = default_split_params.copy()
    else:
        #Update split params to incorporate defaults and hte user defined values
        temp_splits = default_split_params.copy() # Create defaults copy
        temp_splits.update(split_params)
        split_params = temp_splits

    #Extracting hline parameters:
    hline_threshold = hline_params["threshold"]
    hline_line_length = hline_params["line_length"]
    hline_line_gap = hline_params["line_length"]
    hline_rng = hline_params["range"]

    # Find hough lines
    theta = np.linspace(-np.pi/18, np.pi/18, 20)            # setting theta to be all vertical lines
    hough_lines = ski.transform.probabilistic_hough_line(frame, threshold = hline_threshold, line_length = hline_line_length, line_gap = hline_line_gap, theta = theta, rng = hline_rng)

    # Extracting split cutoffs for top and bottom plate regions:
    top_cutoff = split_params["top_cutoff"] # largest value, below which lines are deemed to be lines of the top plate
    bottom_cutoff = split_params["bottom_cutoff"] # smallest value, above which lines are deemeed to be lines of the bottom plate

    # Sorting the lines into top and bottom based on the cutoffs.
    top_lines = []  
    bottom_lines = []

    for line in hough_lines:
        p0, p1 = line
        x0, y0 = p0
        x1, y1 = p1

        # Only consider lines that are only within the outer thirds of the frame
        if x0 < w/3 or x0 > w*0.66: 
            if x1 <w/3 or x1 > w*0.66:
                # if lines are below the top_cutoff pixel value, append to top_lines list
                if y0 < top_cutoff and y1 < top_cutoff:
                    top_lines.append(line)
                # if lines are above the bottom_cutoff bizel value, append to bottom_lines list
                elif y0 > bottom_cutoff and y1 > bottom_cutoff:
                    bottom_lines.append(line)
    return top_lines, bottom_lines

def get_top_plate_coords(top_lines: list) -> tuple:
    """Takes all the hough lines that are around the top plate, and identifies the left and right x,y pixel coordinates of the top plate. 
        x coordinates are determined based on lowest (left) and highest (right) values among the hough lines
        Y Coordinates are determined based on the highest value (lowest visual part of frame) among the hough lines
        
    Parameters:
    top_lines: list
        List of hough lines around the top of the plate.
        
    Returns: tuple
        ((x0,y0), (x1,y1))
        x0,y0 = left coordinate
        x1,y1 = right coordinate        
    """
    x_vals = []
    y_vals = []
    # combine all x values and all y values into lists of x and y 
    for line in top_lines:
        p0, p1 = line
        x0, y0 = p0
        x_vals.append(x0)
        y_vals.append(y0)
        x1, y1 = p1
        x_vals.append(x1)
        y_vals.append(y1)

    #Sort lists from low to high
    x_vals.sort()
    y_vals.sort()

    # highest y value = bottom of top plate
    # lowest value = left, highest x value = right. 
    plate_coords = ((x_vals[0], y_vals[-1]), (x_vals[-1], y_vals[-1]))
    return plate_coords

def get_bottom_plate_coords(bottom_lines: list) -> tuple:
    """Takes all the hough lines that are around the bottom plate, and identifies the left and right x,y pixel coordinates of the bottom plate. 
        x coordinates are determined based on lowest (left) and highest (right) values among the hough lines
        Y Coordinates are determined based on the lowest value (highest visual part of frame) among the hough lines
        
    Parameters:
    bottom_lines: list
        List of hough lines around the bottom of the plate.
        
    Returns: tuple
        ((x0,y0), (x1,y1))
        x0,y0 = left coordinate
        x1,y1 = right coordinate        
    """
    x_vals_b = []
    y_vals_b = []
    
    # combine all x values and all y values into lists of x and y 
    for line in bottom_lines:
        p0, p1 = line
        x0, y0 = p0
        x_vals_b.append(x0)
        y_vals_b.append(y0)
        x1, y1 = p1
        x_vals_b.append(x1)
        y_vals_b.append(y1)
    #Sort lists from low to high
    x_vals_b.sort()
    y_vals_b.sort()

    # lowest y value = top of bottom plate
    # lowest value = left, highest x value = right. 
    plate_coords_bottom = ((x_vals_b[0], y_vals_b[0]), (x_vals_b[-1], y_vals_b[0]))
    return plate_coords_bottom


# Final, combination function for plate analysis
def plate_boundary_analysis(frame: np.ndarray, 
                            crop_params: dict, 
                            hline_params: dict = None, 
                            split_params: dict = None):
    contrast_enhanced = enhhance_contrast(frame, crop_params)
    skeletonized = edge_binarize(contrast_enhanced)
    top_lines, bottom_lines = get_hough_lines(skeletonized, hline_params=hline_params, split_params=split_params)
    bottom_coords = get_bottom_plate_coords(bottom_lines)
    print("bottom coordinates", bottom_coords)
    top_coords = get_top_plate_coords(top_lines)
    print("top coordinates", top_coords)
    return top_coords, bottom_coords







# just the y value to check if the height has been reached
def get_top_plate_height_y_coord(frame: np.ndarray,  crop_params: dict, 
                                 sobel_mask_val: float = 0.6, morph_star_kernel_size: int = 10, 
                                 hline_params: dict = None, split_params: dict = None) -> int:
    """Takes RAW extracted frame, and returns the y pixel coordinate of the top plate
    
    Parameters:
    frame: np.ndarray
        RAW extracted frame from cv2

    crop_params: dict
        Dictionary containing pixel coordinates for cropping. Choose coordinates that leave empty space around the plates, and center the plates.        
        Expected Keys:
        - "top": int
            Pixel index at top of frame above top plate 
        - "bottom": int
            Pixel index at bottom of frame, below the length of the plate
        - "left" : int
            Pixel index at left of frame, leaving blank space around the plate
        - "right" : int
            Pixel index at right of frame, leaving blank space around the plate

    sobel_mask_val: float. Optional, default = 0.6
        Value used to define the mask cutoff between the max and mean intensities of the sobel edges.
        Used to filter out all unimportant edges and only keep dominant edges.
    
    morph_star_kernel_size: int. Optional, default = 10 
        The size of the star kernel used for morphology corrections    

    hline_params: dict = None, Optional. Defaults will be loaded if not provided
        Dictionary containing parameters being used for hough-line detection. 
        Expected keys are one or more of:
        - "threshold": int Default= 10
        - "line_length": int Default = 20
        - "range": int Default = 100
        - "line_gap": int Default = 15
            note: see scikit image documentation for hough-lines to understand what these inputs mean.

    split_params: dict = None, Optional but recommended. Defaults will be loaded if not provided
        Dictionary containing parameters being used to sort top lines corresponding to the top plate and bottom plate
        Expected keys are one or more of:
        - "top_cutoff": int Default = 400. 
                This is a pixel value along the y axis somewhere below the top plate. Recommended: Height of image/2
        - "bottom_cutoff": int Default = 450. 
                This is a pixel value along the y axis below the top_cutoff value, but above the bottom plate. Recommended: Height of image/2 + 100
    
    Returns: int
        Pixel coordinate of top plate
    """
    # Enhance contrast
    contrast_enhanced = enhhance_contrast(frame,  crop_params = crop_params)
    # Detect edges and skeletonize
    edges = edge_binarize(contrast_enhanced, sobel_mask_val=sobel_mask_val, morph_star_kernel_size=morph_star_kernel_size)
    # Find lines corresponding to top plate via hough line detection
    top_lines, bottom_lines = get_hough_lines(edges, hline_params=hline_params, split_params=split_params)
    # grab y value of the top plate
    p0, p1 = get_top_plate_coords(top_lines)
    return p0[1]

def end_height_reached(test_height: int, end_height: int, threshold: int = 5) -> bool:
    """ Compares top plate heights between test frame and final frame (true end height) to determine whether current frame's top plate has reached final height.
    Parameters:
    test_height: int
        y pixel coordinate value of top plate from frame being analyzed
    end_height: int
        y pixel coordinate value of top plate from last frame of video denoting true final height
    Threshold: int, Optional. Default = 5
        Maximum accepted difference between end height and test height
    
    Returns: bool"""
    return test_height <= end_height + threshold



# Find calibration parameters
def get_plate_d_px(plate_coords_bottom: tuple) -> int:
    """
    Takes the left and right coordinates for the bottom plate and computes the diameter of the plate in pixels.
    
    Parameters:
    plate_coords_bottom: tuple
        ((x0,y0), (x1,y1))
        x0,y0 = left coordinate
        x1,y1 = right coordinate
    
    Returns: int
        Plate diameter, in pixels
    """
    p0, p1 = plate_coords_bottom
    lx = p0[0]
    rx = p1[0]
    plate_d = abs(rx-lx)
    return plate_d

def get_pix_to_mm(plate_coords_bottom: tuple, plate_d_mm: float) -> float:
    """ Takes the left and right coordinates for the bottom plate, and the known diameter of plate (mm) to compute the pixel to mm value
    Parameters:
    plate_coords_bottom: tuple
        ((x0,y0), (x1,y1))
        x0,y0 = left coordinate
        x1,y1 = right coordinate
    plate_d_mm: float
        Known diameter of plate, in mm

    Returns: float
        mm/px
    """
    plate_d_px = get_plate_d_px(plate_coords_bottom=plate_coords_bottom)
    px_to_mm = plate_d_mm/plate_d_px
    return px_to_mm