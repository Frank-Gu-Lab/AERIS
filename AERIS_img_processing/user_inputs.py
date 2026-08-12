
"""
 Collects information from user and asks for feedback about processing.

"""


import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import copy
import skimage as ski

# AERIS files
from . import preprocessing as preproc
from . import plate_analysis as plate
from . import metadata_structure as md
from . import filament_contours as fil_contours

from .filament_contours import DEFAULT_CONTOUR_PARAMETERS 
from .plate_analysis import DEFAULT_HLINE_PARAMS




AERIS_SETUP_INFO = ["separation_distance_mm", 
                    "plate_diameter_mm", 
                    "strike_time_ms", 
                    "expt_duration_ms", 
                    "frame_rate_fps"]

# File info acquisition:
def get_file_loc() ->Path:
    filepath = input("Paste file path here:")
    return Path(filepath)

def file_to_analyze(fnames:list)->tuple:
    """ Tuple of start index, end index. 
    Assumes normal indexing, where 1 = first file."""
    total_f = len(fnames)
    print("Which files would you like to analyze?")
    files = input("Input either the number (>0), a range(>0) e.g. (3-7), or 'all'").strip().lower()
    try:
        if "all" in files:
            to_analyze = (0, total_f)
        elif "-" in files:
            inds = files.split("-")
            to_analyze = (int(inds[0])-1, int(inds[1]))
        else:
            to_analyze = (int(files)-1, int(files))
    except:
        print("Invalid input. Please try again.")
        return file_to_analyze(fnames)
    files_to_analyze = fnames[to_analyze[0]:to_analyze[1]]
    for f in files_to_analyze:
        print(f"Files to analyze: {f}")
    return to_analyze


def show_filename(fnames:list):
    print(f"{len(fnames)} files to analyze")
    for f in fnames:
        print(f)

# Processing step:
def which_processing_step() -> str:
    step = input("Do you want to determine A. plate boundaries and cropping, B. find contours, or C. both? Enter A, B or C").strip().lower()
    if step == "a":
        return "plate"
    elif step == "b":
        return "contours"
    elif step == "c":
        return "both"
    else:
        print("Please enter A, B or C")
        return which_processing_step()
    

# Experiment information acquisiont:
def get_expt_setup_info_user(filename) -> dict:
    acq_params_local = copy.deepcopy(md.acq_params_template)
    print(f"Analyzing filename: {filename}")
    for key in acq_params_local:
        if key in AERIS_SETUP_INFO:
            try:
                val = input(f"Enter {key}. Please enter the number, or s to skip: ").strip()
                if val.lower() == "s" or val == "":
                    continue
                else:
                    acq_params_local[key] = float(val)
            except ValueError:
                print("Invalid input. Please enter a number.")
                return get_expt_setup_info_user()
    return acq_params_local

def get_expt_setup_info_excel():
    ...

def get_extraction_interval(total_frames, start_frame) -> int:
    try:
        interval = int(input(f"Max frames = {total_frames - start_frame}. Enter extraction interval (every n'th frame) >=1: ").strip())
        print(interval)
        return interval
    except:
        print("Please enter a valid number")
        return get_extraction_interval()

# Parameter acquisition
def get_params_to_update() -> str:
    """ Asks user which of initial cropping parameters they wnat to try to fix"""
    to_update = input("What would you like to change?\n A. Cropping\n B. Hough line params\n C. Split params\n Enter A, B or C")
    if to_update.lower() == "a":
        tofix = "crop_params"
    elif to_update.lower() == "b":
        tofix = "hough_line_params"
    elif to_update.lower() == "c":
        tofix = "split_params"
    return tofix

def get_crop_params(frame:np.ndarray) -> dict:
    """To obtain user-defined crop indices. Shows user the frame, takes user through steps to obtain crop indices.
    Parameters:
    frame: np.ndarray
        Raw extracted frame by cv2.
    
    Returns: dict
        Dictionary of crop parameters with keys:
        - "top": int
            Pixel index at top of frame above top plate. 
        - "bottom": int
            Pixel index at bottom of frame, below the length of the plate
        - "left": int
            Pixel index at left of frame, leaving blank space around the plate
        - "right": int
            Pixel index at right of frame, leaving blank space around the plate"""
    # convert to grayscale
    frame = preproc.frame_to_grayscale(frame)
    # initiate crop parameters dictionary
    crop_params={"top": None,
                 "bottom": None,
                  "left": None,
                   "right": None}
    good_cropxy = False
    good_cropz = False
    while not good_cropxy:
        # Obtain left and right crop indices
        # Display full frame
        plt.figure(figsize=(4,6))
        plt.imshow(frame, cmap ="gray")
        plt.title("Inspect and provide left and right crop indices\n Choose indices that center and leave empty space around the plates\nclose the window when ready")
        plt.tight_layout()
        plt.show()
        # Get coordinates:
        left = int(input("Enter left pixel index:"))
        right = int(input("Enter right pixel index:"))
        # Display crop to confirm
        cropped_frame = frame[:, left:right]
        plt.figure(figsize=(4,6))
        plt.imshow(cropped_frame, cmap = "gray")
        plt.title("Preview: confirm sample is centered and in middle third of frame.\n Close to adjust or move on.")
        plt.tight_layout()
        plt.show()
        satisfied = input("Does the crop look good? (Y/N)")
        if satisfied.lower() == "y":
            #updating dictionary and breaking loop
            good_cropxy = True
            crop_params.update({"left": left,
                               "right": right})
            print("Saved crop parameters:", crop_params)
            plt.close()
        else:
            # Crop doesn't look good, trying again
            print("No problem, try again.")
    while not good_cropz:
        # display figure
        plt.figure(figsize = (4,6))
        plt.imshow(frame[:, left:right], cmap = "gray")
        plt.title("Inspect and provide top and bottom crop indices\n Choose indices that center and leave empty space around the plates\nclose the window when ready")
        plt.tight_layout()
        plt.show()
        # Get coordinates:
        print("Enter coordinates")
        top = int(input("Enter top pixel index:"))
        bottom = int(input("Enter bottom pixel index:"))
        # Display crop to confirm
        plt.figure(figsize = (4,6))
        plt.imshow(frame[top:bottom, left:right], cmap = "gray")  
        plt.title("Preview:. Close to adjust or move on.")
        plt.tight_layout()
        plt.show()
        satisfied = input("Does the crop look good? (Y/N)")
        if satisfied.lower() == "y":
            # Updating dictionary and breaking loop
            good_cropz = True
            crop_params.update({"top": top,
                               "bottom": bottom})
            print("Saved crop parameters:", crop_params)
            plt.close()   
        else:
            # crop doesn't look good, trying again.
            print("No problem, try again.")   
    return crop_params

def get_new_cont_params(contour_params: dict = None) -> dict:
    """ Collects new parameters contour parameters from user:
    Parameters: 
        contour_params: dict, Optional. Defaults loaded if not provided
            Expected keys are one or more of
                "gauss_sigma" = Float
                "gamma" = int
                "morph_disk_kernel_size" = int
                "min_contour_l" = int
            """
    if contour_params is None:
        # load defaults
        current_params = DEFAULT_CONTOUR_PARAMETERS.copy()
    else:
        # some provided
        temp = DEFAULT_CONTOUR_PARAMETERS.copy()
        temp.update(contour_params)
        current_params = temp
    
    # get new parameters
    new_params = {}
    for key in current_params:
        val = input(f"Current {key} = {current_params[key]}. Enter value to update, or s to skip.")
        if val.lower() == "s" or val == "":
            new_params[key] = current_params[key]
        else:
            try:
                expected_type = type(current_params[key])
                new_params[key] = expected_type(val)
            except:
                print("Please enter a valid input. Keeping current parameters")
                new_params[key] = current_params[key]

    return new_params

def get_new_hline_params(hline_params: dict = None) -> dict:
    """Collects new hline parameters from user
    Parameters:
        hline_params: dict, optional
            Dictionary containing parameters being used for hough-line detection
            Expected keys are
            - "threshold": int Default= 10
            - "line_length": int Default = 20
            - "range": int Default = 100
            - "line_gap": int Default = 15
            note: see scikit image documentation for hough-lines to understand what these inputs mean.

    Returns:dict 
        Updated dictionary containing parameters being used for hough-line detection. 
        - "threshold"
        - "line_length"
        - "range"
        - "line_gap"
            note: see scikit image documentation for hough-lines to understand what these inputs mean."""
    if hline_params == None:
        current_hline_params = DEFAULT_HLINE_PARAMS.copy()
    else:
        current_hline_params = hline_params
    # Display original hline params and collect new
    new_hline_params = {}
    for key in current_hline_params:
        val = input(f"Current {key} = {current_hline_params[key]}\n"
                     f"Default = {DEFAULT_HLINE_PARAMS[key]}\n"
                     "Input new, or enter s to skip:")
        if val.lower() == "s" or val == "":
            # User skipped it, keeping current value
            new_hline_params[key] = current_hline_params[key]
        else:
            try:
                # Update to new value
                new_hline_params[key] = int(val)
            except ValueError:
                print("Invalid input. Keeping current value.")
                new_hline_params[key] = current_hline_params[key]
    return new_hline_params

def get_new_split_params(cropped_frame: np.ndarray, split_params: dict = None) -> dict:
    """ Collects new image split boundaries for finding top and bottom plates from user
    Parameters:
        cropped_frame: np.ndarray
            Cropped frame, grayscale
        spit_params: dict, Optional
            Dictionary containing parameters being used to sort top lines corresponding to the top plate and bottom plate
            - "top_cutoff": int Default = Height of image/2. 
                    This is a pixel value along the y axis somewhere below the top plate. 
            - "bottom_cutoff": int Default = Height of image/2+100. 
                    This is a pixel value along the y axis below the top_cutoff value, but above the bottom plate.
    Returns: dict
            Dictionary containing parameters being used to sort top lines corresponding to the top plate and bottom plate
            - "top_cutoff"
            - "bottom_cutoff"
            """
    h,w = cropped_frame.shape
    # getting defaults
    defaults = plate.get_default_split_params(h)

    if split_params == None:
        current_split_params = defaults
    else:
        current_split_params = split_params
    
    # collecting new params
    new_split_params = {}
    for key in current_split_params:
        plt.figure()
        plt.imshow(cropped_frame, cmap = "gray")
        plt.plot((0,w), (current_split_params[key], current_split_params[key]), color = "red")
        plt.title(f"Current {key} = {current_split_params[key]}\n close to continue")
        plt.show()
        val = input("Input new, or enter s to skip:")
        if val.lower() == "s" or val == "":
            new_split_params[key] = current_split_params[key]
        else:
            try:
                new_split_params[key] = int(val)
            except ValueError:
                print("Invalid input. Keeping current value.")
                new_split_params[key] = current_split_params[key]
    return new_split_params





# Analysis verificaiton

def check_plate_coords(frame: np.ndarray, crop_params: dict, top_coords: tuple, bottom_coords: tuple) -> bool:
    """Render the plate boundaries on plate to confirm if lines look good enough.
    Parameters: 
        frame: np.ndarray
            Raw frame as extracted by cv2
        crop_params: dict
            Dictionary containing pixel coordinates for cropping. Choose coords that leave empty space around and center the plates.
            Expected Keys:
            - "top": int
                Pixel index at top of frame above top plate 
            - "bottom": int
                Pixel index at bottom of frame, below the length of the plate
            - "left" : int
                Pixel index at left of frame, leaving blank space around the plate
            - "right" : int
                Pixel index at right of frame, leaving blank space around the plate  
        top_coords: tuple
            top plate's coordinates ((x0,y0), (x1, y1))
        bottom_coords: tuple
            bottom plate's coordinates ((x0,y0), (x1, y1))
    
    Returns: bool
        True if user confirms good detection. 
        """
    good_detection = False
    # prepare figure for showing
    cropped = preproc.cropped_grayscale(frame = frame, crop_params= crop_params)
    # render figure with lines
    plt.figure()
    plt.imshow(cropped, cmap = "gray")
    # show top line
    plt.plot((top_coords[0][0], top_coords[1][0]), (top_coords[0][1], top_coords[1][1]), linewidth = 1, color = "red")
    # show bottom line
    plt.plot((bottom_coords[0][0], bottom_coords[1][0]), (bottom_coords[0][1], bottom_coords[1][1]), linewidth = 1, color = "red")
    plt.title("Confirm correct plate height and width")
    plt.show()
    # Prompt user for analyze
    check = input("Good plate bound detection? (Y/N)")
    if check.lower() == "y":
        # Yes all good
        good_detection = True
    elif check.lower() == "n": 
        # No, needs to be redone
        good_detection = False
    else:
        print("Please enter Y or N")

    return good_detection

def adjust_params(frame:np.ndarray,
                  crop_params: dict,
                  hline_params: dict,
                  split_params: dict) -> tuple[dict]:

    tofix = get_params_to_update()
    if tofix == "crop_params":
        crop_params = get_crop_params(frame = frame) # get new crop parameters. Want to save to a .json file.
    elif tofix == "hough_line_params":
        hline_params = get_new_hline_params(hline_params = hline_params)
    elif tofix == "split_params":
        contrast_enhanced = plate.enhhance_contrast(frame = frame, crop_params=crop_params)
        split_params = get_new_split_params(contrast_enhanced, split_params = split_params)
    return crop_params, hline_params, split_params

def user_check_contours() ->bool:
    """ Asks user to confirm if the right number of contours got chosen. """
    fixed = False
    check = input("Is it detecting contours correctly? (Y/N)") 
    if check.lower() == "y":
        fixed = True
    return fixed                  

def bad_contour()->bool:
    """Gives user the option to break out of contour analysis loop. Prompted when contour analysis fails. """
    user_break = False
    if input("Break out of loop? (Y/N). Y will terminate analysis").lower() == "y":
        user_break = True
    return user_break


# Troubleshooting
def contour_troubleshooting(frame: np.ndarray, 
                            crop_params: dict,
                            contour_params: dict = None):
    
    # min contour_l parameter extraction
    if contour_params is None:
                min_contourl = fil_contours.DEFAULT_CONTOUR_PARAMETERS["min_contour_l"]
    else:
        min_contourl = contour_params["min_contour_l"]

    # create cropped, binarized frame
    binarized = fil_contours.caber_find_edges(frame, crop_params = crop_params, contour_params= contour_params)

    # find all contours
    contours = ski.measure.find_contours(binarized)

    # Show user the contours
    plt.figure(figsize = (2,2))
    plt.imshow(binarized, cmap = "gray")
    c = 1
    for cont in contours:
        if len(cont)> min_contourl:
            plt.plot(cont[:,1], cont[:, 0], linewidth = 1, color = "red")
            plt.text(x = 320, y = c*100, s = f"Contour {c} length= {len(cont)}")
        c+=1
    plt.title(f"Troubleshoot contours, close to continue")
    plt.show()