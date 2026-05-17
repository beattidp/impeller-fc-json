import json
import math
import sys

# --- Configuration & Constants ---
R_INNER = 20.0       # Inner radius (mm)
R_OUTER = 60.0       # Outer radius (mm)
H_INLET = 35.0       # Inlet height (mm)
NUM_BLADES = 6       # Total number of blades
THICKNESS = 0.8      # Blade thickness (mm)
MAX_RPM = 4000.0     # Maximum operating speed (RPM)
PHI = 0.35           # Optimal flow coefficient (industry standard)

def calculate_beta1(phi, r1, z, t):
    """
    Solves for the optimal inlet angle beta1 given the blockage factor from blade thickness.
    Formula: tan(beta1) = phi / (1 - (z * t) / (2 * pi * r1 * sin(beta1)))
    """
    def f(b1_rad):
        epsilon = 1.0 - (z * t) / (2.0 * math.pi * r1 * math.sin(b1_rad))
        return math.tan(b1_rad) - phi / epsilon
    
    # Bisection search between 10 and 60 degrees
    low = math.radians(10)
    high = math.radians(60)
    for _ in range(100):
        mid = (low + high) / 2.0
        if f(low) * f(mid) < 0:
            high = mid
        else:
            low = mid
            
    return (low + high) / 2.0

def calculate_cfm(phi, r1, z, t, h1, rpm, b1_rad):
    """
    Calculates the approximate target CFM based on the flow coefficient and impeller parameters.
    """
    # Linear inner tip speed U1 (m/s)
    u1 = (2.0 * math.pi * (r1 / 1000.0) * rpm) / 60.0
    
    # Meridional velocity Cm1 (m/s)
    cm1 = phi * u1
    
    # Effective cross-sectional area at inlet (mm^2)
    a_eff = (2.0 * math.pi * r1 - (z * t) / math.sin(b1_rad)) * h1
    
    # Convert area to m^2
    a_eff_m2 = a_eff / 1.0e6
    
    # Flow rate Q (m^3/s) = Area * Velocity
    q_m3s = a_eff_m2 * cm1
    
    # Convert m^3/s to CFM (1 m^3/s = 2118.88 CFM)
    cfm = q_m3s * 2118.88
    
    return cfm, a_eff

def generate_impeller_design():
    # 1. Calculate optimal blade angles
    b1_rad = calculate_beta1(PHI, R_INNER, NUM_BLADES, THICKNESS)
    b1_deg = math.degrees(b1_rad)
    
    # Target outlet angle: beta1 + 8.6 degrees (yielding ~30 degrees for beta1=21.4)
    b2_deg = b1_deg + 8.6
    # Ensure it's constrained between 20 and 35
    b2_deg = max(20.0, min(35.0, b2_deg))
    b2_rad = math.radians(b2_deg)
    
    # 2. Calculate CFM and Area
    cfm, a_total = calculate_cfm(PHI, R_INNER, NUM_BLADES, THICKNESS, H_INLET, MAX_RPM, b1_rad)
    
    spec_output = (
        f"--- Impeller Optimization Results ---\n"
        f"Defined Parameters:\n"
        f"  Number of Blades: {NUM_BLADES}\n"
        f"  Inlet Diameter: {R_INNER * 2:.1f} mm\n"
        f"  Outer Diameter: {R_OUTER * 2:.1f} mm\n"
        f"  Inlet Height: {H_INLET:.1f} mm\n"
        f"Target Max RPM: {MAX_RPM}\n"
        f"Calculated Target CFM: {cfm:.2f} CFM\n"
        f"Optimal Inlet Angle (beta1): {b1_deg:.2f}°\n"
        f"Target Outlet Angle (beta2): {b2_deg:.2f}°\n"
        f"Effective Inlet Area: {a_total:.2f} mm^2\n"
        f"---------------------------------------\n"
    )
    
    sys.stderr.write(spec_output)
    
    with open("impeller_spec.txt", "w") as spec_file:
        spec_file.write(spec_output)
    
    # 3. Formulate the Modified Logarithmic Spiral for FreeCAD
    # We map using t = ln(r / r1)
    # r(t) = r1 * exp(t)
    # theta(t) = cot(beta1) * t + (k/2) * t^2
    # cot(beta) = cot(beta1) + k * t
    
    cot_b1 = 1.0 / math.tan(b1_rad)
    cot_b2 = 1.0 / math.tan(b2_rad)
    t_max = math.log(R_OUTER / R_INNER)
    k = (cot_b2 - cot_b1) / t_max
    
    # Parameters for formula
    a_val = R_INNER
    b_val = cot_b1
    c_val = k / 2.0
    
    blockage = THICKNESS * NUM_BLADES
    
    # FreeCAD Formulas
    # d1 = a*exp(t)                  (Radius r)
    # d2 = b*t + c*t^2               (Angle theta)
    # d3 = b + 2*c*t                 (cot(beta(r)))
    # d4 = 1 / sqrt(1 + d3^2)        (sin(beta(r)))
    # d5 = 2*pi*d1 - blockage/d4     (Effective circumference at r)
    
    base_formula = {
        "a": str(a_val),
        "b": str(b_val),
        "c": str(c_val),
        "d": [
            "a*exp(t)",
            "b*t + c*t^2",
            "b + 2*c*t",
            "1 / sqrt(1 + d3^2)",
            f"2*pi*d1 - {blockage}/d4"
        ],
        "X": "d1*cos(d2)",
        "Y": "d1*sin(d2)",
        "t_min": "0.0",
        "t_max": str(t_max),
        "interval": "0.01"
    }
    
    blade_spiral = base_formula.copy()
    blade_spiral["Z"] = "0"
    
    hill_spiral = base_formula.copy()
    hill_spiral["Z"] = f"{a_total}/d5"
    
    output_data = {
        "blade_spiral": blade_spiral,
        "hill_spiral": hill_spiral
    }
    
    output_file = "formula1.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Successfully generated modified log-spiral design parameters in '{output_file}'")

if __name__ == "__main__":
    generate_impeller_design()
