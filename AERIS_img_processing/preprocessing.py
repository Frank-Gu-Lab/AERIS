# Contains all common preprocessing , frame extraction, and general data extraction functions

import os
import glob

import cv2
import skimage as ski
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Collect experiment information

def get_framecount(file: Path) -> int:
    """ Get total number of frames
    Parameters:
        file: Path
            Windows path to file
    Returns: int
        Total number of frames acquired"""
    # open video
    cap = cv2.VideoCapture(file)
    # Determine total frames
    fc = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return int(fc)

def get_start_frame(file: Path, expt_length: float, frame_rate: float) -> int:
    """ Determines start frame when plate has reached max height based on the length of the experiment
    Parameters:
        file: Path
            Windows path to file
        expt_length: float
            Duration of your experiment after plate reached max height in ms
        frame_rate: float
            frame rate in frames per second
    
    Returns: int
        Frame number to start extracting from"""
    total_frames = get_framecount(file)
    start_frame = int(total_frames - ((frame_rate/1000)*expt_length))
    return start_frame

def get_t(frame_ind: int, n: int, t_col: int) -> float:

    """ Calculates the time point for each frame analyzed in processing pipeline.
    frame_ind = frame index from list of frames. 0th index will be t = 0 
    n = interval between frames that was saved into the list of frames. (Globally defined)
    t_col = frame rate in frames per second
    returns: time t in ms
    """
    t_per_frame = n * (1/t_col)*1000
    t = t_per_frame * frame_ind
    return t

# Extract frames
def fetch_one_frame(file: Path, i: int) -> np.ndarray:
    """ Extracts one frame using cv2
    Parameters:
        file: Path
            Windows path to file
        i: int 1 to total number of frames. 
            Frame you want to extract. Last frame = 1, first frame = total number of frames
            This moves in reverse order
    Returns: np.ndarray
        Frame of interest
    """
    # Open video
    cap = cv2.VideoCapture(file)

    # Check if the video was opened successfully
    if not cap.isOpened():
        print("Error: Could not open video file.")
    else:
        print("Video file opened successfully!")

    total_frames = get_framecount(file) # get total number of frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames-i) # move to last frame

    # extract last frame
    ret, frame = cap.read()
    if ret:
        got_frame = frame
        print("Extracted frame")
    else:
        print("did not open last frame")

    cap.release()
    return got_frame

def extract_frames(file: Path, expt_length: int, n: int = 1, start_frame:int = None)->list:
    """Extracts frames from video
    Parameters:
        file: Path
            Windows path to file
        expt_length: int
            Duration of your experiment after plate reached max height in ms
        n: int (>1), optional. Default is 1
            Interval for extracting frames.
            1 for all frames, otherwise, will extract ever nth frame.
        start_frame: int, Optional.
            Frame number to start extracting from.
            Unless specified, will be calculated by default as total frames - experiment length. 
    Returns: list
        list of frames where each frame is stored as an np.ndarray in BGR format.
            """
    # open video
    cap = cv2.VideoCapture(file)
    # Check if video was successfully opened:
    if not cap.isOpened():
        print("Error: Could not open video file.")
    else:
        print("Video file opened successfully!")

    # initializing
    if start_frame == None:
        start_frame = get_start_frame(file=file, expt_length=expt_length)
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame) # Move to starting frame
    imgs = []                                   # list of np.ndarrays to store frames
    fr_num = start_frame                        # setting frame number to the chosen start frame --- # DO I EVEN NEED THIS!?

    # Extract each chosen frame into list.
    while True:
        ret, frame = cap.read()
        if ret:
            if fr_num % n == 0:
                imgs.append(frame)
            fr_num +=1
        else:
            print(f"did not open frame {fr_num}")
            print(f"saved {len(imgs)} frames out of {fr_num} frames")
            break
    
    return imgs

# Basic image processing
def frame_to_grayscale(frame:np.ndarray) ->np.ndarray:
    """Takes the raw frame extracted by CV2, and converts it to grayscale to be used for scikit image"""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)      # Convert from BGR to RGB
    grayscale = ski.color.rgb2gray(rgb_frame)               # Convert to grayscale
    return grayscale


def cropped_grayscale(frame: np.ndarray, crop_params: dict) -> np.ndarray:
    """ Takes a raw frame of the video in BGR format (for cv2), and converts it to a grayscale format compatible for use with scikit image.
    Useful for quickly viewing image and for future processing 
    
    Parameters: 
    frame: np.ndarray
        This is the raw frame from cv2

    crop_params: dict 
        Dictionary containing pixel coordinates for cropping the image. Coordinates should be chosen to leave empty space around the plates.
        top/bottom plate pair in question must be as close to centered as possible
        
        Expected Keys
        - "top": int
            Pixel index at top of frame above top plate. 
        - "bottom": int
            Pixel index at bottom of frame, below the length of the plate
        - "left": int
            Pixel index at left of frame, leaving blank space around the plate
        - "right": int
            Pixel index at right of frame, leaving blank space around the plate

    Returns: np.ndarray
        cropped frame in grayscale for use with skimage"""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)      # Convert from BGR to RGB
    grayscale = ski.color.rgb2gray(rgb_frame)               # Convert to grayscale

    # extract crop parameters
    t = crop_params["top"]
    b = crop_params["bottom"]
    l = crop_params["left"]
    r = crop_params["right"]

    cropped = grayscale[t:b, l:r]                   # Cropping default old:  grayscale[300:900, 160:310]  
    return cropped




