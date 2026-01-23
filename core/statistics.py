"""
Statistics Module
Simple functions for calculating equipment statistics and trends
"""

from datetime import datetime, timedelta


def calculate_temperature_statistics(readings_list):
    """
    Calculate temperature statistics from a list of readings.
    
    Args:
        readings_list (list): List of reading dicts
    
    Returns:
        dict: Statistics including min, max, avg, trend
    """
    # Extract valid temperatures
    supply_temps = [r['supply_temp'] for r in readings_list if r.get('supply_temp') is not None]
    return_temps = [r['return_temp'] for r in readings_list if r.get('return_temp') is not None]
    deltas = [r['delta_t'] for r in readings_list if r.get('delta_t') is not None]
    
    # Helper function to calculate stats for a list
    def get_stats(temps):
        if not temps:
            return {'min': None, 'max': None, 'avg': None, 'count': 0}
        
        return {
            'min': min(temps),
            'max': max(temps),
            'avg': round(sum(temps) / len(temps), 1),
            'count': len(temps)
        }
    
    # Calculate trend (rising, stable, falling)
    trend = 'stable'
    if len(supply_temps) >= 2:
        first_half = supply_temps[:len(supply_temps)//2]
        second_half = supply_temps[len(supply_temps)//2:]
        
        if first_half and second_half:
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            diff = second_avg - first_avg
            if diff > 1:
                trend = 'rising'
            elif diff < -1:
                trend = 'falling'
    
    return {
        'supply': get_stats(supply_temps),
        'return': get_stats(return_temps),
        'delta_t': get_stats(deltas),
        'trend': trend
    }


def calculate_pressure_statistics(readings_list):
    """
    Calculate refrigerant pressure statistics.
    
    Args:
        readings_list (list): List of reading dicts
    
    Returns:
        dict: Pressure statistics
    """
    discharge = [r['discharge_psi'] for r in readings_list if r.get('discharge_psi') is not None]
    suction = [r['suction_psi'] for r in readings_list if r.get('suction_psi') is not None]
    superheat = [r['superheat'] for r in readings_list if r.get('superheat') is not None]
    subcooling = [r['subcooling'] for r in readings_list if r.get('subcooling') is not None]
    
    def get_stats(values):
        if not values:
            return {'min': None, 'max': None, 'avg': None, 'count': 0}
        return {
            'min': min(values),
            'max': max(values),
            'avg': round(sum(values) / len(values), 1),
            'count': len(values)
        }
    
    return {
        'discharge': get_stats(discharge),
        'suction': get_stats(suction),
        'superheat': get_stats(superheat),
        'subcooling': get_stats(subcooling)
    }


def calculate_efficiency_metrics(readings_list, mode='Cooling'):
    """
    Calculate efficiency metrics based on readings.
    
    Args:
        readings_list (list): List of reading dicts
        mode (str): Operating mode to calculate for
    
    Returns:
        dict: Efficiency score and recommendations
    """
    # Filter readings for this mode
    mode_readings = [r for r in readings_list if r.get('mode') == mode]
    
    if not mode_readings:
        return {
            'mode': mode,
            'readings_count': 0,
            'score': None,
            'status': 'no_data'
        }
    
    score = 100
    issues = []
    
    # Check Delta-T (should be 12-20 for cooling)
    delta_ts = [r['delta_t'] for r in mode_readings if r.get('delta_t') is not None]
    if delta_ts:
        avg_delta = sum(delta_ts) / len(delta_ts)
        if avg_delta < 10:
            score -= 20
            issues.append('Low Delta-T - poor cooling capacity')
        elif avg_delta > 25:
            score -= 15
            issues.append('High Delta-T - possible airflow restriction')
    
    # Check superheat/subcooling consistency
    superheats = [r['superheat'] for r in mode_readings if r.get('superheat') is not None]
    if superheats:
        superheat_variance = max(superheats) - min(superheats)
        if superheat_variance > 10:
            score -= 10
            issues.append('Variable superheat - possible TXV issue')
    
    # Check compressor runtime
    amp_readings = [r.get('compressor_amps') for r in mode_readings if r.get('compressor_amps')]
    if amp_readings:
        avg_amps = sum(amp_readings) / len(amp_readings)
        max_amps = max(amp_readings)
        
        if max_amps > avg_amps * 1.2:
            score -= 5
            issues.append('Compressor draws vary significantly - possible motor issue')
    
    score = max(0, min(100, score))
    
    # Determine efficiency status
    if score >= 85:
        status = 'Excellent'
    elif score >= 70:
        status = 'Good'
    elif score >= 55:
        status = 'Fair'
    else:
        status = 'Poor'
    
    return {
        'mode': mode,
        'readings_count': len(mode_readings),
        'score': score,
        'status': status,
        'issues': issues
    }


def calculate_runtime_statistics(readings_list):
    """
    Calculate runtime and operational statistics.
    
    Args:
        readings_list (list): List of reading dicts
    
    Returns:
        dict: Runtime statistics
    """
    # Count by mode
    modes = {}
    for reading in readings_list:
        mode = reading.get('mode', 'Unknown')
        modes[mode] = modes.get(mode, 0) + 1
    
    # Total readings and time span
    total_readings = len(readings_list)
    
    # Calculate runtime hours from cumulative data if available
    total_runtime = 0
    runtime_readings = [r['runtime_hours'] for r in readings_list if r.get('runtime_hours') is not None]
    if runtime_readings:
        total_runtime = max(runtime_readings)  # Max value is cumulative
    
    # Fault frequency
    fault_readings = [r for r in readings_list if r.get('fault_code')]
    fault_rate = (len(fault_readings) / total_readings * 100) if total_readings > 0 else 0
    
    return {
        'total_readings': total_readings,
        'modes': modes,
        'cumulative_runtime_hours': total_runtime,
        'fault_rate_percent': round(fault_rate, 1),
        'most_common_mode': max(modes, key=modes.get) if modes else None
    }


def get_summary_statistics(readings_list):
    """
    Get comprehensive summary statistics for equipment.
    
    Args:
        readings_list (list): List of reading dicts
    
    Returns:
        dict: All statistics
    """
    if not readings_list:
        return {
            'status': 'no_data',
            'readings_count': 0
        }
    
    return {
        'readings_count': len(readings_list),
        'temperature': calculate_temperature_statistics(readings_list),
        'pressure': calculate_pressure_statistics(readings_list),
        'cooling_efficiency': calculate_efficiency_metrics(readings_list, 'Cooling'),
        'heating_efficiency': calculate_efficiency_metrics(readings_list, 'Heating'),
        'runtime': calculate_runtime_statistics(readings_list),
        'time_span': {
            'first': readings_list[0].get('ts'),
            'last': readings_list[-1].get('ts')
        }
    }
