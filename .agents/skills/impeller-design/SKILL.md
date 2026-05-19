---
name: impeller-design
description: support impeller design and performance prediction
---

## Resources
The `resources/` directory contains critical mathematical foundations and theoretical documentation for impeller design:

- **Engineering Theory Documents (`.pdf`, `.odt`, `.txt`)**: Documents like `Impeller-Design-for-FreeCAD` contain the core engineering theory, mathematical formulas, and parameters for designing impellers. **Review these files to understand the engineering constraints before generating design parameters.**
- **Implementation Guides (`.txt`, `.md`)**: Documents like `FreeCAD-drawing-curves-based-on-functions.txt` contain instructions on translating the mathematical formulas into FreeCAD-compatible curves.

## Workflow

### 0. Operating Conditions
  - Rotational Speed: Operating RPM
  - Target Flow Rate: Desired CFM (Cubic Feet per Minute)

### 1. Geometry Parameters Calculation
  - Calculate optimal blade angles based on Operating RPM and Desired CFM:
    - Optimal Inlet blade angle: β1
    - Optimal Outlet blade angle: β2
  - Additional Geometry Parameters:
    - Inlet Parameters: diameter (d1), blade height (h1), blade wrap angle (θ1)
    - Outlet Parameters: diameter (d2), blade height (h2), blade wrap angle (θ2)
    - Blade Parameters: Number of blades (Z), Blade thickness (t), Blade curvature (c)

### 2. Design impeller
  - Inputs:
    - Calculated Geometry Parameters (d1, d2, β1, β2, etc.)
  - Process:
    - Map out the blade path using a **Logarithmic Spiral**, utilizing the calculated β1 and β2 angles to determine the optimal curvature.
  - Outputs:
    - Blade profile data
   
### 3. Predict performance
  - Inputs:
    - Blade profile data
    - Operating conditions: Operating RPM, Desired CFM, pressure ratio, etc.
  - Outputs:
    - Performance data: such as head, efficiency, etc.

### 4. Analyze performance
  - Inputs:
    - Performance data: such as head, efficiency, etc.
  - Outputs:
    - Performance analysis report

### 5. Optimize performance
  - Inputs:
    - Performance analysis report
  - Outputs:
    - Optimized geometry parameters

### 6. Generate json for freecad
  - Inputs:
    - Optimized geometry parameters
  - Outputs:
    - JSON data for FreeCAD
