# File management imports
import os
import sys
import glob
from pathlib import Path
import importlib
import json
import copy

# Image processing packages
import cv2
import skimage as ski
from skimage import io

# Data analysis packages
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# # Importing functions from the .py files I created for AERIS analysis
from AERIS_img_processing import data_io as data_io
from AERIS_img_processing import metadata_structure
from AERIS_img_processing import preprocessing as preproc
from AERIS_img_processing import plate_analysis as plate
from AERIS_img_processing import filament_contours as fil_contours
from AERIS_img_processing import user_inputs as aeris_ui


#############
### SETUP ###
#############


filepath = aeris_ui.get_file_loc()


# Get the video files 
vids, fnames = data_io.get_videos(filepath)
aeris_ui.show_filename(fnames)
s, e = aeris_ui.file_to_analyze(fnames)

# Get the analysis folder
if not data_io.analysis_folder_exists(filepath):
    print("Checked for analysis folder: Does not exist.")
    data_io.create_analysis_folder(filepath)
    print("created analysis folder")
analysis_folder = data_io.get_analysis_folder(filepath)
print(f"Got analysis folder: {analysis_folder.name}")

# Determine processing steps choice
step = aeris_ui.which_processing_step()
print(f"Processing step choice: {step}")

# Find the metadata file, or create one, then open. 
if not data_io.metadata_file_exists(filepath):
    print("Checked for metadata file, does not exist.")
    data_io.create_metadata_file(filepath)
    print("Created empty metadata file")

# note to self: this function makes an empty file.
# do not initialize metadata structure until AFTER finishing the cropping and plate analysis
# Otherwise all the logic below to check if a set of results or parameters already exists will pass falsely. 
# there is probably a cleaner way to do this - I have a redundancy below. 

json_file = data_io.get_json_file(filepath)

for f in range(s,e):

    ###################################
    #### GET EXPERIMENT PARAMETERS ####
    ###################################

    # Getting AERIS experiment parameters
        # These can either be pulled from an excel/csv file, or input from user. 

    if data_io.acq_params_exists(json_file, fnames[f]):
        # already there
        if data_io.expt_setup_info_exists(json_file, fnames[f]):
            acq_params = data_io.load_acq_params(json_file, fnames[f])
            print("Acquisition parameters already loaded")
   
    elif data_io.expt_excel_exists():
        # pull from excel
        acq_params = data_io.excel_to_acq_params()
        print("Acquisition parameters loaded from excel")

    else: 
        # get user input
        print("User input required for acquisition parameters")
        acq_params = aeris_ui.get_expt_setup_info_user(filename = fnames[f]) # dictionary of experiment parameters



    if step == "plate":

        ####################################################
        #### START CROPPING AND PLATE BOUNDARY ANALYSIS ####
        ####################################################

        # Loading analysis parameters. 
        if data_io.analysis_params_exists(json_file, fnames[f]):
            # already there
            analysis_params = data_io.load_analysis_params(json_file, fnames[f])
            print("Analysis parameters already loaded")
        else:
            # setup from template
            print("Initializing analysis parameters from template")
            analysis_params = data_io.initialize_analysis_params() # dictionary of analysis parameters

        acq_params["total_frames"] = preproc.get_framecount(file = vids[f])
        analysis_params["start_frame"] = preproc.get_start_frame(file = vids[f], 
                                                                 expt_length = acq_params["expt_duration_ms"],
                                                                 frame_rate = acq_params["frame_rate_fps"] )

        # Extract one frame
        frame = preproc.fetch_one_frame(vids[f], 1)

        # Get analysis parameters
        crop_params = aeris_ui.get_crop_params(frame)
        hline_params = analysis_params["hline_params"]
        split_params = analysis_params["split_params"]

        # Get plate coordinates
        all_params_acquired = False
        while not all_params_acquired:
            top_coords, bottom_coords = plate.plate_boundary_analysis(frame = frame,
                                                                      crop_params = crop_params,
                                                                      hline_params = hline_params,
                                                                      split_params = split_params)
        
            good_detection = aeris_ui.check_plate_coords(frame = frame, 
                                                        crop_params=crop_params, 
                                                        top_coords=top_coords,
                                                        bottom_coords=bottom_coords)
            if good_detection:
                all_params_acquired = True
            else:
                crop_params, hline_params, split_params = aeris_ui.adjust_params(frame = frame,
                                                                                crop_params=crop_params,
                                                                                hline_params=hline_params,
                                                                                split_params=split_params)

        # save analysis parameters
        analysis_params.update({"crop_params": crop_params,
                                "hline_params": hline_params,
                                "split_params": split_params})
        
        # save plate_results:s
        plate_results = data_io.initialize_plate_results()
        plate_results["top_plate_coords"] = top_coords
        plate_results["bottom_plate_coords"] = bottom_coords
        plate_results["mm_per_px"] = plate.get_pix_to_mm(plate_coords_bottom=bottom_coords, 
                                                         plate_d_mm = acq_params["plate_diameter_mm"])
        

        print("acq_params=", acq_params, "analysis params = ", analysis_params, "plate results=", plate_results)
        # update metadata file:
        data_io.update_metadata_file(json_file, fnames[f], 
                                     acq_params=acq_params,
                                     analysis_params=analysis_params,
                                     plate_results=plate_results)
       
        print(f"Completed obtaining plate boundaries, and results to {json_file.name}")



    if step == "contours":
        ################################
        #### START CONTOUR ANALYSIS ####
        ################################
        try:
            data_dict = data_io.open_metadata(json_file = json_file)[fnames[f]]
            print("loaded metadata for experiment")
            extraction_info = data_dict["acquisition_params"]
            analysis_info = data_dict["analysis_params_user"]
            plate_info = data_dict["plate_results"]
        except KeyError:
            print("Please complete plate boundary analysis first.")

        n = aeris_ui.get_extraction_interval(total_frames = extraction_info["total_frames"],
                                             start_frame = analysis_info["start_frame"])
        imgs = preproc.extract_frames(file=vids[f],
                                      expt_length = extraction_info["expt_duration_ms"],
                                      n = n,
                                      start_frame = analysis_info["start_frame"])
        print("Extracted all frames, updating metadata")
        extraction_info.update({"extraction_interval": n,
                                "num_extracted_frames": len(imgs)})
        

        crop_params = analysis_info["crop_params"]
        contour_params = analysis_info["contour_params"]

        # Contour analysis
        analysis_complete = False
        while not analysis_complete:
            frame_contours, failure_index = fil_contours.extract_contours(imgs = imgs,
                                                            crop_params = crop_params,
                                                            top_plate_y = int(plate_info["top_plate_coords"][0][1]),
                                                            bottom_plate_y= int(plate_info["bottom_plate_coords"][0][1]),
                                                            contour_params = contour_params)
            if failure_index is None:
                analysis_info.update({"contour_params": contour_params})
                analysis_complete = True
            else:
                fixed = False
                while not fixed:
                    aeris_ui.contour_troubleshooting(imgs[failure_index],
                                                     crop_params=crop_params,
                                                     contour_params=contour_params)
                    fixed = aeris_ui.user_check_contours()
                    if not fixed:
                        contour_params = aeris_ui.get_new_cont_params(contour_params=contour_params)
                        # safeguard to ask user if they want to break out of analysis in case something is going wrong.
                        user_break = aeris_ui.bad_contour()
                        if user_break:
                            analysis_complete = True
                            print("Contour analysis aborted by user.")
                            break
        
        contour_dataset = fil_contours.combine_contours(frame_contours=frame_contours)
        print(f"combined all contours to create array with shape {contour_dataset.shape}")

        # Save dataset and update metadata
        data_io.save_contours(analysis_folder = analysis_folder, 
                              filename = fnames[f],
                              contour_dataset=contour_dataset)
        

        data_io.update_metadata_file(json_file, fnames[f], 
                                     acq_params=extraction_info,
                                     analysis_params=analysis_info,
                                     plate_results=plate_info)
        




    #Both.
    if step == "both":
        print("Under construction. Please run plate and contour analysis separately for now.")