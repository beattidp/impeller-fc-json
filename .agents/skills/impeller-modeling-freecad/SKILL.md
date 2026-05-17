---
name: impeller-modeling-freecad
description: support impeller modeling in FreeCAD by generating JSON data suitable for use by the Parametric_Curve_FP macro.
---

## Resources
- **Parametric_Curve_FP Macro**: Located in `resources/Parametric_Curve_FP/`. This directory contains the macro script (`Parametric_Curve_FP.py`), example `json.txt` configurations, and a `README.md`. **Review the `README.md` in this directory to understand the exact JSON schema required by the macro.**

## Workflow

### 1. Generate JSON for FreeCAD
  - Inputs:
    - Geometry parameters: such as inlet/outlet diameter, blade height, blade angles, etc. (from impeller-design)
  - Process: Map the geometry parameters to the JSON format specified in `resources/Parametric_Curve_FP/README.md`.
  - Outputs:
    - A JSON file formatted for the macro.

### 2. Test in FreeCAD
  - Inputs:
    - The generated JSON data.
  - Process: Ask the user to open FreeCAD, execute the `Parametric_Curve_FP.py` macro with the generated JSON data, and verify the generation of the parametric curve. Wait for the user to provide feedback on the acceptance of the generated model.
  - Outputs:
    - User feedback and validation.