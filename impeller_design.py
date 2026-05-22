import json
import math
import sys

# --- Configuration & Constants ---
MATERIAL_THICKNESS = 2.4 # Base and shroud thickness
R_INNER = 20.0       # Inner radius (mm)
R_OUTER = 60.0       # Outer radius (mm)
H_INLET = 35.0 - MATERIAL_THICKNESS  # Inlet height (mm)
NUM_BLADES = 6       # Total number of blades
THICKNESS = 1.6      # Blade thickness (mm)
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
    
    # Target outlet angle: beta1 + 8.6 degrees
    b2_deg = b1_deg + 8.6
    b2_deg = max(20.0, min(35.0, b2_deg))
    b2_rad = math.radians(b2_deg)
    
    # 2. Calculate CFM and Area
    cfm, a_total = calculate_cfm(PHI, R_INNER, NUM_BLADES, THICKNESS, H_INLET, MAX_RPM, b1_rad)
    
    spec_output = (
        f"--- Impeller Optimization Results ---\n"
        f"Defined Parameters:\n"
        f"  Number of Blades: {NUM_BLADES}\n"
        f"  Blade Thickness: {THICKNESS} mm\n"
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
    
    # 3. Formulate the Modified Logarithmic Spiral
    cot_b1 = 1.0 / math.tan(b1_rad)
    cot_b2 = 1.0 / math.tan(b2_rad)
    t_max = math.log(R_OUTER / R_INNER)
    k = (cot_b2 - cot_b1) / t_max
    
    a_val = R_INNER
    b_val = cot_b1
    c_val = k / 2.0
    blockage = THICKNESS * NUM_BLADES
    
    # Calculate bounds for trailing curve
    def get_rtrail(t):
        rt = a_val * math.exp(t)
        cot_b = b_val + 2.0 * c_val * t
        cos_b = cot_b / math.sqrt(1.0 + cot_b**2)
        r2 = rt**2 + THICKNESS**2 - 2.0 * rt * THICKNESS * cos_b
        return math.sqrt(max(0, r2))
        
    def solve_t(target_r, t_guess):
        low, high = t_guess - 1.0, t_guess + 1.0
        for _ in range(100):
            mid = (low + high) / 2.0
            f_low = get_rtrail(low) - target_r
            f_mid = get_rtrail(mid) - target_r
            if f_low * f_mid < 0:
                high = mid
            else:
                low = mid
        return (low + high) / 2.0

    t_min_trail = solve_t(R_INNER, 0.0)
    t_max_trail = solve_t(R_OUTER, t_max)
    
    d_list_lead = [
        "a*exp(t)",                       # d1: radius r
        "b*t + c*t^2",                    # d2: theta
        "b + 2*c*t",                      # d3: cot(beta)
        "1 / sqrt(1 + d3^2)",             # d4: sin(beta)
        f"2*pi*d1 - {blockage}/d4",       # d5: effective circumference (legacy)
        "d3 * d4",                        # d6: cos(beta) = cot(beta)*sin(beta)
        "-(d4*sin(d2) + d6*cos(d2))",     # d7: NX
        "d4*cos(d2) - d6*sin(d2)",        # d8: NY
        "d1",                             # d9: actual radius R
        "b + 2*c*log(d9/a)",              # d10: cot(beta) at actual radius R
        "1 / sqrt(1 + d10^2)",            # d11: sin(beta) at actual radius R
        f"2*pi*d9 - {blockage}/d11",      # d12: effective circumference at actual radius R
    ]
    
    d_list_trail = [
        "a*exp(t)",                       # d1: radius r
        "b*t + c*t^2",                    # d2: theta
        "b + 2*c*t",                      # d3: cot(beta)
        "1 / sqrt(1 + d3^2)",             # d4: sin(beta)
        f"2*pi*d1 - {blockage}/d4",       # d5: effective circumference (legacy)
        "d3 * d4",                        # d6: cos(beta) = cot(beta)*sin(beta)
        "-(d4*sin(d2) + d6*cos(d2))",     # d7: NX
        "d4*cos(d2) - d6*sin(d2)",        # d8: NY
        f"sqrt(d1^2 + {THICKNESS}^2 - 2*d1*{THICKNESS}*d6)",  # d9: actual radius R for offset curve
        "b + 2*c*log(d9/a)",              # d10: cot(beta) at actual radius R
        "1 / sqrt(1 + d10^2)",            # d11: sin(beta) at actual radius R
        f"2*pi*d9 - {blockage}/d11",      # d12: effective circumference at actual radius R
    ]

    base_formula = {
        "a": str(a_val),
        "b": str(b_val),
        "c": str(c_val)
    }
    
    blade_spiral_leading = dict(base_formula, **{
        "d": d_list_lead,
        "X": "d1*cos(d2)",
        "Y": "d1*sin(d2)",
        "Z": "0",
        "t_min": "0.0",
        "t_max": str(t_max),
        "interval": "0.01"
    })
    
    hill_spiral_leading = dict(base_formula, **{
        "d": d_list_lead,
        "X": "d1*cos(d2)",
        "Y": "d1*sin(d2)",
        "Z": f"{a_total}/d12",
        "t_min": "0.0",
        "t_max": str(t_max),
        "interval": "0.01"
    })
    
    blade_spiral_trailing = dict(base_formula, **{
        "d": d_list_trail,
        "X": f"d1*cos(d2) + {THICKNESS} * d7",
        "Y": f"d1*sin(d2) + {THICKNESS} * d8",
        "Z": "0",
        "t_min": str(t_min_trail),
        "t_max": str(t_max_trail),
        "interval": "0.01"
    })
    
    hill_spiral_trailing = dict(base_formula, **{
        "d": d_list_trail,
        "X": f"d1*cos(d2) + {THICKNESS} * d7",
        "Y": f"d1*sin(d2) + {THICKNESS} * d8",
        "Z": f"{a_total}/d12",
        "t_min": str(t_min_trail),
        "t_max": str(t_max_trail),
        "interval": "0.01"
    })
    
    output_data = {
        "blade_spiral_leading": blade_spiral_leading,
        "hill_spiral_leading": hill_spiral_leading,
        "blade_spiral_trailing": blade_spiral_trailing,
        "hill_spiral_trailing": hill_spiral_trailing
    }
    
    output_file = "formula1.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Successfully generated 4-profile design parameters in '{output_file}'")

if __name__ == "__main__":
    generate_impeller_design()
