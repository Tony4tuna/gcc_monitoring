"""
Equipment Analysis Module
Simple, readable functions for analyzing HVAC equipment readings
"""

def _ensure_dict(reading):
    """Convert sqlite3.Row to dict if needed"""
    if hasattr(reading, 'keys'):  # sqlite3.Row has keys method
        return dict(reading)
    return reading


def _to_float(value):
    """Convert value to float, returns None if conversion fails"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def get_temperature_analysis(supply_temp, return_temp):
    """
    Analyze temperature readings.
    
    Args:
        supply_temp (float): Supply temperature in Fahrenheit
        return_temp (float): Return temperature in Fahrenheit
    
    Returns:
        dict: Analysis with delta_t, status, and warnings
    """
    # Convert to float
    supply_temp = _to_float(supply_temp)
    return_temp = _to_float(return_temp)
    
    # Handle missing data
    if supply_temp is None or return_temp is None:
        return {
            'delta_t': None,
            'status': 'no_data',
            'warning': 'Missing temperature readings'
        }
    
    # Calculate temperature difference
    delta_t = supply_temp - return_temp
    
    # Analyze based on value
    analysis = {
        'delta_t': delta_t,
        'supply_temp': supply_temp,
        'return_temp': return_temp,
        'status': 'normal',
        'warning': None
    }
    
    # Check for warnings
    if delta_t < 10:
        analysis['status'] = 'warning'
        analysis['warning'] = 'Low Delta-T (poor temperature differential)'
    elif delta_t > 25:
        analysis['status'] = 'warning'
        analysis['warning'] = 'High Delta-T (possible restriction)'
    
    return analysis


def get_pressure_analysis(discharge_psi, suction_psi, mode):
    """
    Analyze refrigerant pressures.
    
    Args:
        discharge_psi (float): Discharge pressure
        suction_psi (float): Suction pressure
        mode (str): Operating mode (Cooling, Heating, etc)
    
    Returns:
        dict: Analysis with pressure ratio and status
    """
    # Convert to float
    discharge_psi = _to_float(discharge_psi)
    suction_psi = _to_float(suction_psi)
    
    if discharge_psi is None or suction_psi is None:
        return {
            'status': 'no_data',
            'warning': 'Missing pressure readings'
        }
    
    # Typical pressure ratios by mode
    normal_ratios = {
        'Cooling': {'min': 4, 'max': 6},
        'Heating': {'min': 3, 'max': 5},
    }
    
    # Calculate pressure ratio
    if suction_psi > 0:
        ratio = discharge_psi / suction_psi
    else:
        ratio = None
    
    analysis = {
        'discharge_psi': discharge_psi,
        'suction_psi': suction_psi,
        'ratio': ratio,
        'status': 'normal',
        'warning': None
    }
    
    # Check if ratio is out of normal range
    if ratio is not None and mode in normal_ratios:
        min_ratio = normal_ratios[mode]['min']
        max_ratio = normal_ratios[mode]['max']
        
        if ratio < min_ratio:
            analysis['status'] = 'warning'
            analysis['warning'] = f'Low pressure ratio: {ratio:.1f} (expected {min_ratio}-{max_ratio})'
        elif ratio > max_ratio:
            analysis['status'] = 'warning'
            analysis['warning'] = f'High pressure ratio: {ratio:.1f} (expected {min_ratio}-{max_ratio})'
    
    return analysis


def get_electrical_analysis(phase_1, phase_2, phase_3, compressor_amps):
    """
    Analyze electrical readings.
    
    Args:
        phase_1 (float): Phase 1 current in amps
        phase_2 (float): Phase 2 current in amps
        phase_3 (float): Phase 3 current in amps
        compressor_amps (float): Compressor current draw
    
    Returns:
        dict: Analysis with balance and overload warnings
    """
    # Convert to float
    phase_1 = _to_float(phase_1)
    phase_2 = _to_float(phase_2)
    phase_3 = _to_float(phase_3)
    compressor_amps = _to_float(compressor_amps)
    
    # Handle missing data
    phases = [phase_1, phase_2, phase_3]
    phase_values = [p for p in phases if p is not None]
    
    if not phase_values:
        return {
            'status': 'no_data',
            'warning': 'Missing electrical readings'
        }
    
    analysis = {
        'phase_1': phase_1,
        'phase_2': phase_2,
        'phase_3': phase_3,
        'compressor_amps': compressor_amps,
        'status': 'normal',
        'warning': None,
        'avg_amps': None,
        'imbalance': None
    }
    
    # Calculate average
    avg = sum(phase_values) / len(phase_values)
    analysis['avg_amps'] = round(avg, 2)
    
    # Check phase imbalance (ideal: within 5%)
    if len(phase_values) == 3:
        max_phase = max(phase_values)
        min_phase = min(phase_values)
        imbalance_percent = ((max_phase - min_phase) / avg * 100) if avg > 0 else 0
        analysis['imbalance'] = round(imbalance_percent, 1)
        
        if imbalance_percent > 10:
            analysis['status'] = 'warning'
            analysis['warning'] = f'Phase imbalance: {imbalance_percent:.1f}% (should be <10%)'
    
    # Check compressor overload (typical max 120% of rated)
    if compressor_amps and avg > 0:
        overload_percent = (compressor_amps / avg * 100) - 100
        if overload_percent > 20:
            analysis['status'] = 'warning'
            analysis['warning'] = f'Compressor overload: {compressor_amps}A at {overload_percent:.0f}% above average'
    
    return analysis


def calculate_equipment_health_score(readings):
    """
    Calculate overall equipment health score (0-100).
    
    Args:
        readings (dict or sqlite3.Row): Equipment reading with all parameters
    
    Returns:
        dict: Health score with breakdown by category
    """
    # Convert Row to dict if needed
    readings = _ensure_dict(readings)
    score = 100  # Start at perfect
    issues = []
    
    # Temperature analysis (30% of score)
    temp = get_temperature_analysis(readings.get('supply_temp'), readings.get('return_temp'))
    if temp.get('status') == 'warning':
        score -= 15
        issues.append(temp['warning'])
    elif temp.get('status') == 'no_data':
        score -= 10
    
    # Pressure analysis (30% of score)
    pressure = get_pressure_analysis(
        readings.get('discharge_psi'),
        readings.get('suction_psi'),
        readings.get('mode')
    )
    if pressure.get('status') == 'warning':
        score -= 15
        issues.append(pressure['warning'])
    elif pressure.get('status') == 'no_data':
        score -= 10
    
    # Electrical analysis (20% of score)
    electrical = get_electrical_analysis(
        readings.get('v_1'),
        readings.get('v_2'),
        readings.get('v_3'),
        readings.get('compressor_amps')
    )
    if electrical.get('status') == 'warning':
        score -= 10
        issues.append(electrical['warning'])
    elif electrical.get('status') == 'no_data':
        score -= 5
    
    # Fault code penalty (20% of score)
    if readings.get('fault_code'):
        score -= 20
        issues.append(f'Active fault code: {readings["fault_code"]}')
    
    # Ensure score stays in range
    score = max(0, min(100, score))
    
    # Determine health status
    if score >= 80:
        health_status = 'Excellent'
    elif score >= 60:
        health_status = 'Good'
    elif score >= 40:
        health_status = 'Fair'
    elif score >= 20:
        health_status = 'Poor'
    else:
        health_status = 'Critical'
    
    return {
        'score': score,
        'status': health_status,
        'issues': issues,
        'temperature': temp,
        'pressure': pressure,
        'electrical': electrical
    }
