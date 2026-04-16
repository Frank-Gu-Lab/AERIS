"""
Handles all the imports and exports

"""
from pathlib import Path
import numpy as np
import json
import copy

from . import user_inputs as aeris_ui
from . import metadata_structure as md
from .metadata_structure import metadata_template

not_vid_folders = ["00_processed", "00 processed", "archive"]


####  VIDEO HANDLING

def valid_folder(f:Path)->bool:
    """ Checks to see if the folder is a PFV video folder."""
    screen = not_vid_folders.copy()
    valid = True # Assume true till proven false
    for _ in screen:
        if _.lower() in f.name.lower():
            # if found, break
            valid = False
            break
    return valid

def get_all_folders(filepath: Path) -> list[Path]:
    folder_list = [f for f in filepath.iterdir() if f.is_dir()]
    return folder_list

def get_video_folders(filepath:Path)->list[Path]:
    folder_list = [f for f in filepath.iterdir() if f.is_dir()]
    vid_folder_list = [f for f in folder_list if valid_folder(f)]
    return vid_folder_list

def get_video_files(filepath: Path)->list[Path]:
    file_locs = get_video_folders(filepath = filepath)
    filelst = []
    for f in file_locs:
        for v in f.glob("*mp4"):
            filelst.append(v)
    return filelst

def get_video_filenames(files) -> list[str]:
    filenames = [f.name for f in files]
    return filenames

def get_videos(filepath:Path)->tuple[Path,str]:
    """ Returns (videos, filenames), where videos are the .mp4 files"""
    videos = get_video_files(filepath = filepath)
    filenames = get_video_filenames(videos)
    return videos, filenames



#### DATA ANALYSIS FOLDER:

def analysis_folder_exists(filepath:Path)-> bool:
    """Looks for if the analysis folder exists."""
    folders = get_all_folders(filepath=filepath) 
    exists = False
    for f in folders:
        if "processed" in f.name:
            exists = True
            break
    return exists

def create_analysis_folder(filepath: Path)->Path:
    """" makes the analysis folder 
    """
    analysis_folder = filepath / "00_processed"
    analysis_folder.mkdir(exist_ok=True) # only makes it IF the folder doesn't already exist. 
    print("Created 00_processed folder")

def get_analysis_folder(filepath: Path)->Path:
    """ Just grabs the folder. Will return None if it doesn't exist."""
    folder = None
    folders = get_all_folders(filepath=filepath)
    for f in folders:
        if "processed" in f.name:
            folder = f
            break
    if folder is None:
        print("Error: No analysis folder found")
    return folder



#### METADATA IMPORTS
# There's the actual file, and then the data within. 
# Metadata is meant to be structured as one big file for a given experiment, with all data from the videos to be within the same file.

def metadata_file_exists(filepath: Path) -> bool:
    analysis_folder = get_analysis_folder(filepath) #Where the file should be.
    candidates = [f for f in analysis_folder.glob("*json")] # Get all the json files
    if len(candidates) == 0:
        exists = False # Need to make a new one
    else:
        for c in candidates:
            if "expt_analysis_metadata" in c.name:
                exists = True
                break
    return exists

def create_metadata_file(filepath: Path):
    """ Creates an empty metadata file with correct name and structure"""
    analysis_folder = get_analysis_folder(filepath = filepath)
    json_file = analysis_folder/"expt_analysis_metadata.json"
    all_experiments = {} # Contents (an empty dictionary to be populated).
    with open(json_file, "w") as f:
        json.dump(all_experiments, f, indent= 4) #creates file

def get_json_file(filepath: Path)-> Path:
    analysis_folder = get_analysis_folder(filepath = filepath)
    json_file = analysis_folder/"expt_analysis_metadata.json"
    return json_file

def open_metadata(json_file:Path)->dict:
    """ Finds and opens the metadata file"""
    with open(json_file, "r") as f:
        all_experiments = json.load(f) # open the file
        # file is either an empty dictionary, or has some data in it. 
    return all_experiments 

def expt_metadata_exists(json_file:Path, fname:str)->bool:
    """ Looks for if there is any metadata for the given experiment"""
    all_experiments = open_metadata(json_file) # load file - read mode
    if fname in all_experiments:
        return True
    else:
        return False

def initialize_experiment_metadata():
    expt_metadata = copy.deepcopy(md.metadata_template)
    return expt_metadata

def load_experiment_metadata(json_file: Path, fname:str)->dict:
    if expt_metadata_exists(json_file, fname):
        expt_metadata = open_metadata(json_file)[fname] # load file - expt data - read mode
    return expt_metadata

# Acquisition parameters
def acq_params_exists(json_file: dict, fname:str) -> bool:
    """ Checks for an "acquisition_params" entry in metadata JSON file"""
    exists = True
    if not expt_metadata_exists(json_file, fname):
        # if it doesn't exist, then we know acq params don't exist. This is a fail safe
        exists = False
    else:
        # Pull out experiment metadata, look for acq parameters.
        expt_metadata = open_metadata(json_file)[fname] # load file - expt data - read mode
        if "acquisition_params" not in expt_metadata:
            exists = False
    return exists

def load_acq_params(json_file: dict, fname:str) ->dict:
    """ Loads acquisition parameters from metadata JSON file"""
    expt_metadata = open_metadata(json_file)[fname] # load file - expt data - read mode
    acq_params = expt_metadata["acquisition_params"]
    return acq_params

def expt_setup_info_exists(json_file: dict, fname:str) -> bool:
    """ Checks for the presence of acquisition parameters in the metadata JSON file. If not present, then will need to be collected from user or excel."""
    # expt_metadata = open_metadata(json_file)[fname] # load file - expt data - read mode
    acq_params = load_acq_params(json_file = json_file, fname = fname)
    all_params_exist = True
    for key in aeris_ui.AERIS_SETUP_INFO:
        if acq_params[key] is None:
            all_params_exist = False
            break
    return all_params_exist  


def expt_excel_exists():
    ...

def excel_to_acq_params():
    ...



# analysis parameters
def analysis_params_exists(json_file: dict, fname:str):
    """ Checks for an "analysis_params" entry in metadata JSON file"""
    exists = True
    if not expt_metadata_exists(json_file, fname):
        # if it doesn't exist, then we know acq params don't exist. This is a fail safe
        exists = False
    else:
        # Pull out experiment metadata, look for acq parameters.
        expt_metadata = open_metadata(json_file)[fname] # load file - expt data - read mode
        if "analysis_params" not in expt_metadata:
            exists = False
    return exists


def initialize_analysis_params():
    analysis_params = copy.deepcopy(md.analysis_params_template)
    return analysis_params


def load_analysis_params(json_file: dict, fname:str):
    """ Loads analysis parameters from metadata JSON file"""
    expt_metadata = open_metadata(json_file=json_file)[fname]
    analysis_params = expt_metadata["analysis_params"]
    return analysis_params


# plate results

def plate_results_exists(json_file: dict, fname:str):
    """ Checks for a "plate_results" entry in metadata JSON file"""
    exists = True
    if not expt_metadata_exists(json_file, fname):
        # if it doesn't exist, then we know acq params don't exist. This is a fail safe
        exists = False
    else:
        # Pull out experiment metadata, look for acq parameters.
        expt_metadata = open_metadata(json_file)[fname] # load file - expt data - read mode
        if "plate_results" not in expt_metadata:
            exists = False
    return exists


def initialize_plate_results():
    plate_results = copy.deepcopy(md.plate_results_template)
    return plate_results

def load_plate_results(json_file: dict, fname:str):
    """ Loads plate results from metadata JSON file"""
    expt_metadata = open_metadata(json_file=json_file)[fname]
    plate_results = expt_metadata["plate_results"]
    return plate_results




def updt_mdata(params: dict, data:dict) -> dict:
    """ Updates the chosen parameters dictionary with new data provided"""
    params.update(data)
    return params


def update_metadata_file(json_file: Path, fname: str, 
                         acq_params: dict| None = None,
                         analysis_params: dict| None = None,
                         plate_results: dict| None = None):
    
    all_experiments = open_metadata(json_file)

    if not expt_metadata_exists(json_file = json_file, fname=fname):
        all_experiments[fname] = initialize_experiment_metadata()
    
    updates = {"acquisition_params": acq_params,
               "analysis_params_user": analysis_params,
               "plate_results": plate_results}
    
    for key, value in updates.items():
        if value is not None:
            all_experiments[fname][key] = value

    with open(json_file, "w") as f:
        json.dump(all_experiments, f, indent=4)
    print(f"Metadata file updated for experiment: {fname}")


def save_contours(analysis_folder: Path, filename:str, contour_dataset: np.ndarray):
    data_name = analysis_folder/f"{filename.replace(".mp4", "")}_contours.npz"
    np.savez(data_name, contours = contour_dataset)
    print(f"Saved contours to {data_name}")


