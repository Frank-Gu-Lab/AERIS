# AERIS Opentrons Workflow Control

This folder contains the Jupyter notebook containing scripts used to operate
the Opentrons OT-2 liquid handling workflow for AERIS

## Contents
- `aeris_opentrons_control.ipynb`  
  Annotated notebook containing the OT-2 workflow sequence,
  movement commands, and experimental parameters.
- PENDING: topplate rack labware definition
- PENDING: bottom plate rack labware definition

## Requirements
- Opentrons OT-2 robot
- Opentrons Python API (version 2.19)
- A high speed camera such as Photron UX-2 mini connected to the OT-2 via Arduino

## Usage
The notebook can be uploaded to the Opentrons App or adapted for
execution within the OT-2 environment.