# Contains metadata structure


acq_params_template = {"separation_distance_mm": None,
              "plate_diameter_mm": None,
              "strike_time_ms": None,
              "expt_duration_ms": None,
              "total_frames": None,
              "frame_rate_fps": None,
              "extraction_interval": None,
              "num_extracted_frames": None}


analysis_params_template = {"start_frame": None,
                   "crop_params": None,
                   "hline_params": None,
                   "split_params": None,
                   "contour_params": None}


plate_results_template = {"top_plate_coords": None,
                 "bottom_plate_coords": None,
                 "mm_per_px": None}


metadata_template = {"acquisition_params": acq_params_template, # acq_params
            "analysis_params_user": analysis_params_template, # analysis_params
            "plate_results": plate_results_template}     # plate_results