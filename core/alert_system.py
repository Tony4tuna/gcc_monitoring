"""
Alert System Module
Simple rules engine for generating alerts based on readings
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

# Define alert severity levels
ALERT_CRITICAL = 'critical'
ALERT_WARNING = 'warning'
ALERT_INFO = 'info'

# Standard temperature thresholds (Fahrenheit)
TEMP_THRESHOLDS = {
    'min': 32,      # Freezing risk
    'max_supply': 140,  # Supply too hot
    'low_delta_t': 10,  # Poor cooling/heating
    'high_delta_t': 25,
}

# Standard pressure thresholds (PSI)
PRESSURE_THRESHOLDS = {
    'min_discharge': 100,
    'max_discharge': 400,
    'min_suction': 20,
    'max_suction': 150,
}

# Electrical thresholds
ELECTRICAL_THRESHOLDS = {
    'max_phase_amps': 50,
    'max_imbalance_percent': 10,
    'compressor_overload_percent': 20,
}


def check_temperature_alerts(supply_temp, return_temp, mode):
    """
    Check temperature readings for alerts.
    
    Args:
        supply_temp (float): Supply temperature
        return_temp (float): Return temperature
        mode (str): Operating mode
    
    Returns:
        list: List of alert dicts with severity and message
    """
    # Convert to float
    supply_temp = _to_float(supply_temp)
    return_temp = _to_float(return_temp)
    
    alerts = []
    
    if supply_temp is None:
        return alerts  # Skip if no data
    
    # Check for freezing risk
    if supply_temp < TEMP_THRESHOLDS['min']:
        alerts.append({
            'severity': ALERT_CRITICAL,
            'code': 'TEMP_FREEZE_RISK',
            'message': f'Supply temp {supply_temp}°F - Freezing risk',
            'parameter': 'supply_temp'
        })
    
    # Check for overheating
    if supply_temp > TEMP_THRESHOLDS['max_supply']:
        alerts.append({
            'severity': ALERT_WARNING,
            'code': 'TEMP_TOO_HIGH',
            'message': f'Supply temp {supply_temp}°F - Excessive temperature',
            'parameter': 'supply_temp'
        })
    
    # Check delta-t for active cooling/heating
    if return_temp is not None and mode in ['Cooling', 'Heating']:
        delta_t = supply_temp - return_temp
        
        if delta_t < TEMP_THRESHOLDS['low_delta_t']:
            alerts.append({
                'severity': ALERT_WARNING,
                'code': 'LOW_DELTA_T',
                'message': f'Low Delta-T ({delta_t:.1f}°F) - Poor efficiency',
                'parameter': 'delta_t'
            })
        
        if delta_t > TEMP_THRESHOLDS['high_delta_t']:
            alerts.append({
                'severity': ALERT_INFO,
                'code': 'HIGH_DELTA_T',
                'message': f'High Delta-T ({delta_t:.1f}°F) - Possible restriction',
                'parameter': 'delta_t'
            })
    
    return alerts


def check_pressure_alerts(discharge_psi, suction_psi, mode):
    """
    Check refrigerant pressures for alerts.
    
    Args:
        discharge_psi (float): Discharge pressure
        suction_psi (float): Suction pressure
        mode (str): Operating mode
    
    Returns:
        list: List of alert dicts
    """
    # Convert to float
    discharge_psi = _to_float(discharge_psi)
    suction_psi = _to_float(suction_psi)
    
    alerts = []
    
    if discharge_psi is None or suction_psi is None:
        return alerts  # Skip if no data
    
    # Check discharge pressure bounds
    if discharge_psi < PRESSURE_THRESHOLDS['min_discharge']:
        alerts.append({
            'severity': ALERT_WARNING,
            'code': 'LOW_DISCHARGE_PSI',
            'message': f'Low discharge pressure {discharge_psi} PSI - Possible leak',
            'parameter': 'discharge_psi'
        })
    
    if discharge_psi > PRESSURE_THRESHOLDS['max_discharge']:
        alerts.append({
            'severity': ALERT_CRITICAL,
            'code': 'HIGH_DISCHARGE_PSI',
            'message': f'High discharge pressure {discharge_psi} PSI - System overload',
            'parameter': 'discharge_psi'
        })
    
    # Check suction pressure bounds
    if suction_psi < PRESSURE_THRESHOLDS['min_suction']:
        alerts.append({
            'severity': ALERT_WARNING,
            'code': 'LOW_SUCTION_PSI',
            'message': f'Low suction pressure {suction_psi} PSI - Possible blockage',
            'parameter': 'suction_psi'
        })
    
    if suction_psi > PRESSURE_THRESHOLDS['max_suction']:
        alerts.append({
            'severity': ALERT_INFO,
            'code': 'HIGH_SUCTION_PSI',
            'message': f'High suction pressure {suction_psi} PSI',
            'parameter': 'suction_psi'
        })
    
    # Check pressure ratio
    if suction_psi > 0:
        ratio = discharge_psi / suction_psi
        if ratio < 3 or ratio > 7:
            alerts.append({
                'severity': ALERT_WARNING,
                'code': 'UNUSUAL_PRESSURE_RATIO',
                'message': f'Pressure ratio {ratio:.1f} - Outside normal range',
                'parameter': 'pressure_ratio'
            })
    
    return alerts


def check_electrical_alerts(phase_1, phase_2, phase_3, compressor_amps):
    """
    Check electrical readings for alerts.
    
    Args:
        phase_1 (float): Phase 1 amps
        phase_2 (float): Phase 2 amps
        phase_3 (float): Phase 3 amps
        compressor_amps (float): Compressor current
    
    Returns:
        list: List of alert dicts
    """
    # Convert to float
    phase_1 = _to_float(phase_1)
    phase_2 = _to_float(phase_2)
    phase_3 = _to_float(phase_3)
    compressor_amps = _to_float(compressor_amps)
    
    alerts = []
    
    phases = [phase_1, phase_2, phase_3]
    phase_values = [p for p in phases if p is not None]
    
    if not phase_values:
        return alerts  # Skip if no data
    
    # Check individual phase limits
    for i, phase in enumerate(phases, 1):
        if phase and phase > ELECTRICAL_THRESHOLDS['max_phase_amps']:
            alerts.append({
                'severity': ALERT_WARNING,
                'code': f'PHASE_{i}_OVERLOAD',
                'message': f'Phase {i} overload: {phase}A',
                'parameter': f'v_{i}'
            })
    
    # Check phase imbalance
    if len(phase_values) == 3:
        avg = sum(phase_values) / 3
        max_phase = max(phase_values)
        min_phase = min(phase_values)
        
        if avg > 0:
            imbalance = ((max_phase - min_phase) / avg) * 100
            
            if imbalance > ELECTRICAL_THRESHOLDS['max_imbalance_percent']:
                alerts.append({
                    'severity': ALERT_WARNING,
                    'code': 'PHASE_IMBALANCE',
                    'message': f'Phase imbalance: {imbalance:.1f}% (max {ELECTRICAL_THRESHOLDS["max_imbalance_percent"]}%)',
                    'parameter': 'phase_imbalance'
                })
    
    # Check compressor overload
    if compressor_amps and phase_values:
        avg = sum(phase_values) / len(phase_values)
        if avg > 0:
            overload_percent = ((compressor_amps - avg) / avg) * 100
            
            if overload_percent > ELECTRICAL_THRESHOLDS['compressor_overload_percent']:
                alerts.append({
                    'severity': ALERT_WARNING,
                    'code': 'COMPRESSOR_OVERLOAD',
                    'message': f'Compressor overload: {overload_percent:.0f}% above average',
                    'parameter': 'compressor_amps'
                })
    
    return alerts


def evaluate_all_alerts(reading):
    """
    Evaluate all alerts for a single reading.
    
    Args:
        reading (dict or sqlite3.Row): Complete equipment reading
    
    Returns:
        dict: All alerts grouped by severity
    """
    # Convert Row to dict if needed
    reading = _ensure_dict(reading)
    all_alerts = []
    
    # Check each category
    all_alerts.extend(check_temperature_alerts(
        reading.get('supply_temp'),
        reading.get('return_temp'),
        reading.get('mode')
    ))
    
    all_alerts.extend(check_pressure_alerts(
        reading.get('discharge_psi'),
        reading.get('suction_psi'),
        reading.get('mode')
    ))
    
    all_alerts.extend(check_electrical_alerts(
        reading.get('v_1'),
        reading.get('v_2'),
        reading.get('v_3'),
        reading.get('compressor_amps')
    ))
    
    # Add fault code if present
    if reading.get('fault_code'):
        all_alerts.insert(0, {
            'severity': ALERT_CRITICAL,
            'code': 'UNIT_FAULT',
            'message': f'Unit fault: {reading["fault_code"]}',
            'parameter': 'fault_code'
        })
    
    # Group by severity
    return {
        'critical': [a for a in all_alerts if a['severity'] == ALERT_CRITICAL],
        'warning': [a for a in all_alerts if a['severity'] == ALERT_WARNING],
        'info': [a for a in all_alerts if a['severity'] == ALERT_INFO],
        'all': all_alerts,
        'count': len(all_alerts)
    }
