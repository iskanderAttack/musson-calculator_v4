import math
from .constants import MATERIALS, FUEL_TYPES

def calc_heat_loss(area_m2, height_m, wall_thickness_m, material, t_in, t_out, 
                   windows_m2=0, doors_m2=0, roof_insulation=True):
    volume_m3 = area_m2 * height_m
    
    lambda_wall = MATERIALS[material]
    r_wall = wall_thickness_m / lambda_wall
    wall_area = 2 * height_m * (math.sqrt(area_m2) * 4) - windows_m2 - doors_m2
    q_walls = wall_area * (t_in - t_out) / r_wall
    
    q_windows = windows_m2 * (t_in - t_out) / 0.4
    q_doors = doors_m2 * (t_in - t_out) / 0.6
    
    roof_r = 0.2 if not roof_insulation else 1.0
    q_roof = area_m2 * (t_in - t_out) / roof_r
    
    q_vent = 0.3 * volume_m3 * (t_in - t_out)
    
    total_w = q_walls + q_windows + q_doors + q_roof + q_vent
    return total_w / 1000

def musson_power(volume_l, fill_fraction, fuel_type, efficiency, burn_hours):
    vol_m3 = volume_l / 1000
    filled_vol_m3 = vol_m3 * fill_fraction
    m_fuel = filled_vol_m3 * FUEL_TYPES[fuel_type]["density"]
    q_fuel = m_fuel * FUEL_TYPES[fuel_type]["q"]
    q_kwh = q_fuel / 3.6
    useful_kwh = q_kwh * efficiency
    p_kw = useful_kwh / burn_hours
    return useful_kwh, p_kw, m_fuel

def calculate_heating_economics(heat_loss_kw, model_power, working_hours, 
                              fuel_type, efficiency, fuel_price_per_ton):
    if heat_loss_kw <= model_power:
        duty_cycle = heat_loss_kw / model_power
        daily_operating_hours = working_hours * duty_cycle
        daily_heat_kwh = model_power * daily_operating_hours
    else:
        duty_cycle = 1.0
        daily_operating_hours = working_hours
        daily_heat_kwh = model_power * working_hours
    
    fuel_energy_kwh_kg = (FUEL_TYPES[fuel_type]["q"] / 3.6) * efficiency
    daily_fuel_kg = daily_heat_kwh / fuel_energy_kwh_kg
    
    fuel_price_per_kg = fuel_price_per_ton / 1000
    daily_cost = daily_fuel_kg * fuel_price_per_kg
    monthly_cost = daily_cost * 22
    seasonal_cost = monthly_cost * 7
    
    return {
        'daily_fuel_kg': daily_fuel_kg,
        'daily_cost': daily_cost,
        'monthly_cost': monthly_cost,
        'seasonal_cost': seasonal_cost,
        'duty_cycle': duty_cycle,
        'daily_operating_hours': daily_operating_hours,
        'daily_heat_kwh': daily_heat_kwh
    }
