# AERIS Opentrons Workflow Control

This folder contains the Jupyter notebook containing scripts used to operate
the AERIS workflow on the OT-2 liquid handler, and the JSON files for the custom labware components.

## Contents
- Annotated notebook containing the functions functions for and orchestration of the AERIS workflow. (`aeris_opentrons_control.ipynb`)
- Top plate rack labware definition (`caber_topplt_holder_flush.json`)
    NOTE: Fabricated top plates are loaded onto a standard 300 uL Opentrons tip rack
- Bottom plate labware definition (`caber_bottom_plate.json`)
- Cleaning module labware definition (`AERIS_opentrons_workflow_control/fgl_12_tall_drypad_rack.json`)

## Requirements
- Opentrons OT-2 liquid handler equipped with P1000 and P300 pipettes, and hardware.
- Opentrons Python API (version 2.19)
- A high speed camera such as Photron UX-2 mini connected to the OT-2 via Arduino
- a light source place behind the high speed camera


## Guidance on usage
The notebook and associated JSON files should be uploaded to the built-in Opentrons Jupyter Notebook server. The Jupyter Notebook file (`aeris_opentrons_control.ipynb`) should be executed through the Opentrons Jupyter Notebook server, which is set up to (a) Import all necessary libraries (b) Import all necessary hardware, including the custom labware included herein (c) Define the default locations on the bottom CaberPlate (d) define functions that orchestrate the custome movements on the OT-2 deck (e) run the experiment.

## Running an experiment
To run an experiment, follow the steps below in stepwise order. 

(1) Turn on the Photron UX100 mini highspeed camera, and the OT-2.

(2) Open the notebook and run all cells that import hardware and libraries, as well as all cells within the functions and classes section. This process will home the OT-2 gantry, and set up all defaults. 
- NOTE: if you want to change your deck layout, make sure to change the locations within the code. 
- The code is currently setup for manual cleaning. If you would like to automate cleaning, uncomment the `clean(...)` function(s) within `caber_run_iter_visc_autocam(...)` before running these cells. Make sure you also change the sponge pad location to reflect the sponge you want to use.

(3) Perform a positional calibration to ensure your top and bottom plates are aligned and centered on the x and y axis, and such that the two plates just begin to touch. Tip: place a Kimwipe between the two plates when calibrating in the z direction. The point at which the two plates touch would be the point at which you feel resistance when trying to move the Kimwipe from side to side. 

Once you are happy with the alignment, test that positioning is consistent across three separate top plates. If you feel positioning is off, perform the calibration again and repeat. When satisfied with the calibration, you can perform the experiments

(4) Set up the acquisition parameters on the camera:
- Set up auto saving, and tne number of partitions
- Set trigger mode to 'end trigger'
- Set your desired frame rate
- Click record to start recording and enter the save location. At this point the camera will start recording to buffer.

(5) Set up your operational parameters (pipetting speeds and intervals, plate height and actuation time etc.). For detailed information on what needs to be adjusted, and what each argument means, please read all the documentation within the notebook. Make sure you make note of these parameters, especially:
- trig_wait_t
- plate diameter
- actuation time
- end height (h)
You will need them for video processing.

(6) Run! Once an experiment (one well) is complete, the camera will automatically save the video to file. Once this is done, confirm on the OT-2 that the camera is ready. We are currently working to automate this step so that you don't need to babysit the instrument.

(7) Once you've completed your experiments, you can move on to data processing to extract your contours.
