#--------------------------------------------------------------
# Savitsky Method Calculation Module
# Based on: Planing_Hull_in_Calm_Water_Savitsky_Method.m
#--------------------------------------------------------------

import numpy as np
from scipy.optimize import brentq, fsolve
import logging

class Savitsky_Calm_Water:
    
    def __init__(self, params):

        """
        Initialize with ship parameters.
        params: dict containing:
            - g: Gravity (m/s^2)
            - rho: Water density (kg/m^3)
            - nu: Kinematic viscosity (m^2/s)
            - ship_length: Ship length (m)
            - ship_beam: Ship beam (m)
            - mass: Mass (kg)
            - beta: Deadrise angle (degrees)
            - lcg: Longitudinal Center of Gravity (m) from transom
            - vcg: Vertical Center of Gravity (m) from keel
            - draft: Draft (m)
            - frontal_area: Frontal area of ship (m^2)
            - f: Distance between Thrust line and CG (m) - usually 0
            - epsilon: Angle between Thrust line and Keel (degrees) - usually 0
        """

        self.p = params
        self.g = params.get('g', 9.81)
        self.rho = params.get('rho', 1000.0)
        self.nu = params.get('nu', 1.0e-6)
        
        self.L = params['ship_length']
        self.B = params['ship_beam']
        self.M = params['mass']
        self.beta_deg = params['beta']
        self.lcg = params['lcg']
        self.vcg = params['vcg']
        self.draft = params['draft']
        self.Ah = params.get('frontal_area', 0.0)
        self.f = params.get('f', 0.0)
        self.epsilon_deg = params.get('epsilon', 0.0)
        
        # Derived
        self.displacement = self.M * self.g # Weight in Newtons
        self.beta_rad = np.radians(self.beta_deg)
        self.epsilon_rad = np.radians(self.epsilon_deg)

    def _savitsky_formula(self, velocity, trim_angle_deg):
        """
        Internal method to calculate forces and moments for a given speed and trim.
        Equivalent to Savitsky_Method.m function.
        """
        tau_deg = trim_angle_deg
        tau_rad = np.radians(tau_deg)
        
        # Avoid division by zero for very small speeds
        if velocity < 0.1:
            return None

        # Step 1: Beam Froude number and C_Lb
        Cv = velocity / np.sqrt(self.g * self.B)
        CLb = self.displacement / (0.5 * self.rho * (velocity**2) * (self.B**2))

        # Step 2: Lift coefficient of zero deadrise (CL0)
        # Eq: CL0 - 0.0065 * Beta * CL0^0.6 - CLb = 0
        # This equation seems to be: CLb = CL0 - 0.0065 * Beta * CL0^0.6
        # So we solve for CL0 given CLb
        def func_CL0(x):
            if x < 0: return 1e6 # Penalty for negative x
            return x - 0.0065 * self.beta_deg * (x**0.6) - CLb
        
        try:
            CL0 = brentq(func_CL0, 0.0001, 10.0) # Search range
        except ValueError:
            # Fallback if brentq fails (e.g. roots outside range)
            CL0 = fsolve(func_CL0, CLb)[0]

        # Step 3: Mean wetted length-beam ratio (lambda)
        # Eq: CL0 = lambda^1.1 * (0.012 * lambda^0.5 + 0.0055 * lambda^2.5 / Cv^2)
        # Rearranged: 0.012 * lambda^0.5 + 0.0055 * lambda^2.5 / Cv^2 - CL0 / tau^1.1 = 0
        # Note: tau in degrees in the formula from Matlab code: C_L0/Current_tao^1.1
        
        if tau_deg <= 0.1:
            return None # Invalid trim

        def func_lambda(lam):
            if lam < 0: return 1e6
            term1 = 0.012 * (lam**0.5)
            term2 = 0.0055 * (lam**2.5) / (Cv**2)
            term3 = CL0 / (tau_deg**1.1)
            return term1 + term2 - term3

        try:
            lam = brentq(func_lambda, 0.01, 10.0)
        except ValueError:
             # Try to find a root with fsolve if brentq fails
            lam = fsolve(func_lambda, self.L/self.B)[0]

        # Calculate mean velocity on bottom (Vm)
        k = 0.012 * (lam**0.5) * (tau_deg**1.1)
        # Vm formula
        term_vm = (k - 0.0065 * self.beta_deg * (k**0.6)) / (lam * np.cos(tau_rad))
        Vm = velocity * np.sqrt(1 - term_vm)

        # Reynolds number
        Re = Vm * lam * self.B / self.nu

        # Frictional drag coefficient (ITTC 1957 or similar)
        # Matlab uses: 0.075 / (log10(Re)-2)^2
        Cf_base = 0.075 / ((np.log10(Re) - 2)**2)
        Delta_Cf = 0.0004 # Roughness allowance
        Current_Cf = Cf_base + Delta_Cf

        # Frictional drag (Df)
        Df = (self.rho * (Vm**2) * lam * (self.B**2) * Current_Cf) / (2 * np.cos(self.beta_rad))

        # Total Resistance (R) - Hydrodynamic part
        # R = Df / cos(tau) + Displacement * tan(tau)
        R_hydro = Df / np.cos(tau_rad) + self.displacement * np.tan(tau_rad)

        # Center of Pressure (Cp)
        Cp = 0.75 - (lam**2) / (5.21 * (Cv**2) + 2.39 * (lam**2))

        # Distance a (Df to CG normal to Df)
        a = self.vcg - (self.B / 4) * np.tan(self.beta_rad)

        # Distance c (N to CG normal to N)
        # N acts at Cp * lambda * B from transom (along keel)
        # LCG is from transom
        # c = LCG - Cp * lambda * B
        c = self.lcg - Cp * lam * self.B

        # Equilibrium Moment Sum
        # M = D * ((1 - sin(tau)*sin(tau+eps))*c/cos(tau) - f*sin(tau)) + Df*(a - f)
        # Note: Matlab code uses Displacement for D
        term_D1 = (1 - np.sin(tau_rad) * np.sin(tau_rad + self.epsilon_rad)) * c / np.cos(tau_rad)
        term_D2 = self.f * np.sin(tau_rad)
        Moment = self.displacement * (term_D1 - term_D2) + Df * (a - self.f)

        # Wetted Keel Length (Lk)
        Lk = lam * self.B + self.B * np.tan(self.beta_rad) / (2 * np.pi * np.tan(tau_rad))
        
        # Wetted Chine Length (Lc)
        Lc = lam * self.B - self.B * np.tan(self.beta_rad) / (2 * np.pi * np.tan(tau_rad))

        # Draft of keel at transom (d)
        d = Lk * np.sin(tau_rad)

        # Sinkage (Method 1)
        Zwl = self.vcg * np.cos(tau_rad) - (Lk - self.lcg) * np.sin(tau_rad)
        sinkage = Zwl - (self.vcg - self.draft)

        # Following the seakeeping coordinate system, the positive sinkage is downward
        sinkage = -sinkage  


        # Spray Calculation
        # Alpha
        term_alpha = np.pi * np.tan(tau_rad) / (2 * np.tan(self.beta_rad))
        Alpha = np.arctan(term_alpha)
        
        # Gama
        Gama = Alpha + np.arctan((1 - 2/np.pi) * np.sin(Alpha) * np.tan(self.beta_rad))
        
        # Spray Velocity
        V_spray = velocity * np.sin(Gama)
        
        # Spray Dimensions
        Z_spray = (V_spray**2) / (2 * self.g)
        L_H = (V_spray**2) / self.g * np.sin(Gama) * np.cos(Gama)
        X_spray = L_H * np.cos(Alpha)
        Y_spray = L_H * np.sin(Alpha)

        # Whisker Spray Resistance (Rs)
        Theta = 2 * Alpha / np.cos(self.beta_rad)
        Delta_lambda = np.cos(Theta) / (4 * np.sin(2 * Alpha) * np.cos(self.beta_rad))
        Lws = 0.5 * (0.5 * self.B) / (np.sin(2 * Alpha) * np.cos(self.beta_rad))
        Re_Lws = velocity * Lws / self.nu
        
        Cf_ws = 0.0
        if Re_Lws >= 1.5e6:
            Cf_ws = 0.074 / (Re_Lws**0.2) - 4800 / Re_Lws
        else:
            Cf_ws = 1.328 / (Re_Lws**0.5)
            
        Rs = 0.5 * self.rho * (velocity**2) * Delta_lambda * (self.B**2) * Cf_ws

        # Air Resistance (Ra)
        rho_air = 1.225
        Ca = 0.7
        Ra = 0.5 * rho_air * (velocity**2) * self.Ah * Ca

        # Total Resistance
        Rt = R_hydro + Rs + Ra

        return {
            'R_hydro': R_hydro,
            'Rs': Rs,
            'Ra': Ra,
            'Rt': Rt,
            'trim_deg': tau_deg,
            'sinkage': sinkage,
            'lambda': lam,
            'Vm': Vm,
            'Lk': Lk,
            'Lc': Lc,
            'd': d,
            'a': a,
            'c': c,
            'Moment': Moment,
            'Cv': Cv,
            'Fn': velocity / np.sqrt(self.g * self.L),
            'X_spray': X_spray,
            'Y_spray': Y_spray,
            'Z_spray': Z_spray
        }

    def find_equilibrium_trim(self, velocity):
        """
        Find the trim angle where the sum of moments is zero.
        """
        def moment_func(tau):
            res = self._savitsky_formula(velocity, tau)
            if res is None:
                return 1e9 # Penalty
            return res['Moment']

        # Search range for trim [0.5, 15] degrees as per Savitsky limit
        try:
            final_trim = brentq(moment_func, 0.5, 15.0)
        except ValueError:
            # If no root found in range, try to find minimum absolute moment
            # This is a fallback, might indicate unstable or invalid config
            taus = np.linspace(0.5, 15.0, 30)
            moments = [abs(moment_func(t)) for t in taus]
            final_trim = taus[np.argmin(moments)]
            logging.warning(f"Could not find exact equilibrium trim for V={velocity:.2f}. Using best approximation: {final_trim:.2f} deg")

        return self._savitsky_formula(velocity, final_trim)

    def calculate_single_speed(self, velocity):
        """
        Calculate for a single speed.
        """
        return self.find_equilibrium_trim(velocity)

    def calculate_multiple_speeds(self, speeds):
        """
        Calculate for a list of speeds.
        """
        results = []
        for v in speeds:
            res = self.calculate_single_speed(v)
            if res:
                res['velocity'] = v
                results.append(res)
        return results

    def calculate_wake_profile(self, velocity, trim_deg, lambda_val, Cv):
        """
        Calculate wake profile based on Savitsky and Michael 2010.
        
        Args:
            velocity: Ship velocity (m/s)
            trim_deg: Trim angle (degrees)
            lambda_val: Mean wetted length-beam ratio
            Cv: Beam Froude number
            
        Returns:
            dict with 'X', 'Centerline_H', 'Quarterbeam_H' arrays
        """
        # Non-dimensional Lk
        Lk = lambda_val * self.B + self.B * np.tan(self.beta_rad) / (2 * np.pi * np.tan(np.radians(trim_deg)))
        Non_dimensional_Lk = Lk / self.B
        
        # X/B values from 0 to 3.0 with step 0.05
        Wake_Profile_X = np.arange(0.0, 3.05, 0.05)
        
        # Coefficients based on deadrise angle
        if abs(self.beta_deg - 10) < 0.1:  # Beta == 10
            c_centerline = 1.50
            c_quarterbeam = 0.75
        elif abs(self.beta_deg - 20) < 0.1:  # Beta == 20
            c_centerline = 2.00
            c_quarterbeam = 0.75
        else:  # Other angles
            c_centerline = 2.00
            c_quarterbeam = 0.75
        
        # Calculate wake profiles
        term = (Wake_Profile_X / 3.0) ** 1.5
        sin_term = np.sin(np.pi / Cv * term)
        
        Centerline_Wake_Profile_H = 0.17 * (c_centerline + 0.03 * Non_dimensional_Lk * trim_deg**1.5) * sin_term
        Quarterbeam_Wake_Profile_H = 0.17 * (c_quarterbeam + 0.03 * Non_dimensional_Lk * trim_deg**1.5) * sin_term
        
        return {
            'X': Wake_Profile_X,
            'Centerline_H': Centerline_Wake_Profile_H,
            'Quarterbeam_H': Quarterbeam_Wake_Profile_H
        }

if __name__ == "__main__":
    # Test case from Matlab file (Full scale)
    params = {
        'g': 9.81,
        'rho': 1000,
        'nu': 1.0e-6,
        'ship_length': 8.0,
        'ship_beam': 1.6,
        'mass': 3017.4373,
        'beta': 20,
        'lcg': 3.28,
        'vcg': 0.47,
        'draft': 0.4000,
        'frontal_area': 1.3818,
        'f': 0.0,
        'epsilon': 0.0
    }
    
    solver = Savitsky_Calm_Water(params)
    
    # Test speeds
    speeds = [5.2267, 7.8844, 10.5421, 13.1112, 15.7688]
    
    print(f"{'V(m/s)':<10} {'Trim(deg)':<10} {'Rt(N)':<10} {'Sinkage(m)':<10} {'Lambda':<10}")
    print("-" * 55)
    
    results = solver.calculate_multiple_speeds(speeds)
    for res in results:
        print(f"{res['velocity']:<10.4f} {res['trim_deg']:<10.4f} {res['Rt']:<10.4f} {res['sinkage']:<10.4f} {res['lambda']:<10.4f}")
