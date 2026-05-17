import json
import math
import os

# --- Constants for Impeller Design ---
R_INNER = 20.0       # Inner radius (mm)
R_OUTER = 60.0       # Outer radius (mm)
H_INLET = 35.0       # Inlet height (mm)
NUM_BLADES = 6       # Total number of blades
THICKNESS = 0.8      # Blade thickness (mm)
BETA_DEG = 30.0      # Blade angle (degrees)

def generate_impeller_design():
    # Convert beta to radians
    beta_rad = math.radians(BETA_DEG)
    
    # Calculate b for the logarithmic spiral: r = r1 * exp(b * t)
    b_val = math.tan(math.radians(90.0 - BETA_DEG))
    
    # Calculate maximum t to reach R_OUTER
    # R_OUTER = R_INNER * exp(b_val * t_max)
    t_max = math.log(R_OUTER / R_INNER) / b_val
    
    # --- Constant Flow Area Calculation ---
    # Effective tangent distance at inner radius:
    # t_eff(r) = 2 * pi * r * sin(beta) / Z - s_b
    # A_total = Z * t_eff(r1) * h1 = (2 * pi * r1 * sin(beta) - s_b * Z) * h1
    sin_beta = math.sin(beta_rad)
    blockage = THICKNESS * NUM_BLADES
    
    a_total = (2 * math.pi * R_INNER * sin_beta - blockage) * H_INLET
    
    print(f"Calculated A_total: {a_total:.2f} mm^2")
    print(f"Calculated t_max: {t_max:.4f} radians")
    
    # The height profile z(r) needs to satisfy A_total = (2*pi*r*sin(beta) - s_b*Z) * z
    # Let d1 = r = a * exp(b*t)
    # Let d2 = 2 * pi * d1 * sin_beta - blockage
    # Then Z = a_total / d2
    
    blade_spiral = {
        "a": str(R_INNER),
        "b": str(b_val),
        "c": str(a_total),
        "d": [
            "a*exp(b*t)",
            f"2*pi*d1*{sin_beta} - {blockage}"
        ],
        "X": "d1*cos(t)",
        "Y": "d1*sin(t)",
        "Z": "0",
        "t_min": "0.0",
        "t_max": str(t_max),
        "interval": "0.01"
    }

    hill_spiral = {
        "a": str(R_INNER),
        "b": str(b_val),
        "c": str(a_total),
        "d": [
            "a*exp(b*t)",
            f"2*pi*d1*{sin_beta} - {blockage}"
        ],
        "X": "d1*cos(t)",
        "Y": "d1*sin(t)",
        "Z": "c/d2",
        "t_min": "0.0",
        "t_max": str(t_max),
        "interval": "0.01"
    }
    
    output_data = {
        "blade_spiral": blade_spiral,
        "hill_spiral": hill_spiral
    }
    
    output_file = "formula1.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Successfully generated design parameters in '{output_file}'")

if __name__ == "__main__":
    generate_impeller_design()
