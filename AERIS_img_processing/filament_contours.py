# Contains all functions to extract contours of filaments during an AERIS experiment

import cv2
import skimage as ski
from skimage import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import preprocessing as preproc

# Setting defaults:
DEFAULT_CONTOUR_PARAMETERS = {"gauss_sigma": 0.5,
                              "gamma": 5,
                              "morph_disk_kernel_size": 13,
                              "min_contour_l": 300}


def caber_find_edges(frame: np.ndarray, crop_params: dict, contour_params: dict = None) -> np.ndarray:
    """
    Takes a raw frame and returns a binary, cropped image that outlines the edges of the thinning filament.

    Parameters:
        frame: np.ndarray
            raw frame as extracted by cv2
        crop_params: dict
            Contains pixel coordinates for cropping. Choose coordinates that center and leave empty space around the plates.        
            Expected Keys:
            - "top": int
                Pixel index at top of frame above top plate 
            - "bottom": int
                Pixel index at bottom of frame, below the length of the plate
            - "left" : int
                Pixel index at left of frame, leaving blank space around the plate
            - "right" : int
                Pixel index at right of frame, leaving blank space around the plate
        contour_params: dict, Optional
            Expect one or more of keys:  
            gauss_sigma: float, optional. Default is 0.5
                Sigma factor for gaussian blur. Larger values cause more blurring.
                For more information consult scikit image.
            gamma: float, optional. Default value is 5
                For use in gamma correction. Higher values cause darker images.
                For more information consult scikit image. 
            morph_disk_kernel_size: int, optional. Default values is 13
                For morphological opening of binary image.
                Higher values will minimize the amount of whitespace inside the contour that could be cause by glare/overexposing. 
    Returns: np.ndarray
        Binary, cropped image. 
        """

    # find contour parameters or set defaults
    if contour_params == None:
        contour_params = DEFAULT_CONTOUR_PARAMETERS.copy()
    else:
        temp = DEFAULT_CONTOUR_PARAMETERS.copy()
        temp.update(contour_params)
        contour_params = temp
    
    gauss_sigma = contour_params["gauss_sigma"]
    gamma = contour_params["gamma"]
    morph_disk_kernel_size = contour_params["morph_disk_kernel_size"]
    
    # crop
    cropped = preproc.cropped_grayscale(frame, crop_params=crop_params)
    # blur
    blurred = ski.filters.gaussian(cropped, sigma = gauss_sigma)
    # gamma correct
    gammacorr = ski.exposure.adjust_gamma(blurred, gamma = gamma, gain = 1)
    # make binary
    otsuv = ski.filters.threshold_otsu(gammacorr)
    gammacorr = gammacorr > otsuv
    # morphologicla opening
    k = ski.morphology.disk(morph_disk_kernel_size)
    morph = ski.morphology.binary_opening(gammacorr, footprint = k)
    return morph

# Should break this up into a couple of functions - later
def caber_find_contours(frame: np.ndarray, top_plate_y: int, bottom_plate_y:int = 450, contour_params: dict = None) -> tuple[np.ndarray]:
    """Takes a morphology corrected and binary image 
    First, finds the contours, then filters contours to make sure there are only two contours arranged in ascending y value order.
    Returns a tuple of the two contours each an array of [row nums, col nums], where rows = y values and columns = x values of the image that make up the contours
    
    Parameters:
        frame: np.ndarray
            Binary, morphology corrected image that clearly outlines the thinning filament
        top_plate_y: int
            Rough y-coordinate of the top plate. Often from finding the top plate coords. If guessing, then it should be a little taller than the top plate's edge. 
        bottom_plate_y: int , optional. Default is 450
            Rough y-coordinate lower than the bottom plate. 
        contour_params: dict, Optional
           Expect atleast key :
                min_contour_l: int. Default is 300
                    Minimum length the contour needs to be to be considered a contour of the outer edge of the filament. 

    Returns: tuple
        Both contours outlining the filament, where each contour is np.ndarray. 
        Each contour is of the form [[yval1, xval1]
                                     [yval2, xval2]
                                     ...]

    """
    # find contour parameters or set defaults
    if contour_params == None:
        contour_params = DEFAULT_CONTOUR_PARAMETERS.copy()
    else:
        temp = DEFAULT_CONTOUR_PARAMETERS.copy()
        temp.update(contour_params)
        contour_params = temp

    min_contour_l = contour_params["min_contour_l"]

    # Find contours
    contours = ski.measure.find_contours(frame)

    if len(contours) > 2:
        # Sometimes we get more than 2 contours. We only want to keep the two longest contours    
        contours_fil = [c for c in contours if len(c) > min_contour_l] # filtered to keep longest
    else:
        # if we have 2 or fewer, keep all contours
        contours_fil = contours      
    
    if len(contours_fil) > 2:
        # If there are still more than two contours, then print an error    
        print(f"ERROR: there are more than 2 contours. Contours number = {len(contours_fil)}")
    else:
        # All good, only two contours, so know keeping only values confined between the top and bottom plates.    
        y_fil_contours = []
        for c in contours_fil:
            mask = np.logical_and(top_plate_y < c[:,0], c[:,0] < bottom_plate_y)
            filc = c[mask]
            if filc[0][0] > filc[-1][0]:        # automatically appends such that first element has lowest y value
                y_fil_contours.append(filc[::-1])
            else:
                y_fil_contours.append(filc) 

    # making both contours have the same y values:
    a = []
    b = []
    for yx in y_fil_contours[0][:]:
        mask = y_fil_contours[1][:,0] == yx[0]  # finding the coordinates that have shared y values
        yx_b = y_fil_contours[1][mask]
        if len(yx_b) > 0:
            a.append(yx)        # add that coordinate to contour list a
            b.append(yx_b[0])   # add the matching coordinate to contour list b
            
    return np.array(a),np.array(b)

def extract_contours(imgs: list[np.ndarray],
                     crop_params: dict,
                     top_plate_y: int,
                     bottom_plate_y: int,
                     contour_params: dict = None):
    frame_contours = []
    for i, img in enumerate(imgs):
        try:
            binarized = caber_find_edges(frame = img,
                                        crop_params = crop_params,
                                        contour_params = contour_params)
            contour_a, contour_b = caber_find_contours(frame = binarized,
                                                    top_plate_y = top_plate_y,
                                                    bottom_plate_y = bottom_plate_y,
                                                    contour_params = contour_params)
            if contour_a.size == 0 or contour_b.size == 0:
                # filament has broken, end for-loop
                print(f"Filament broken at frame index {i}, analysis complete.")
                break
            else:
                combined = np.column_stack((contour_a[:,0], contour_a[:, 1], contour_b[:, 1])) # combine contours into an array such that we have columns [y, x1, x2]
                frame_contours.append(combined)
                print(f"frame: {i}, contour_length = {combined.shape}")
        except:
            print(f"Contour analysis failed at index {i} - troubleshoot.")
            return None, i
    return frame_contours, None



def combine_contours(frame_contours: list[np.ndarray]) -> np.ndarray:
    """ Combines extracted contours into an array with shape:
    (number of frames, maximum contour_length, 3), where 3 is comprised of:
    y_coordinate with 0 at the top, x1 from contour_a, x2 from contour_b
    """
    # determine total number of frames = length of array
    n_saved_fr = int(len(frame_contours))
    # determine max contour length
    lengths = [len(contour) for contour in frame_contours]
    maximum_yl = int(max(lengths))

    # create array filled with np.nan 
    dataset = np.full((n_saved_fr, maximum_yl, 3), np.nan)

    # fill array with contours
    for i, contour in enumerate(frame_contours):
        dataset[i, :len(contour), :] = contour
    
    return dataset

    

