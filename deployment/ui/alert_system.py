def evaluate_all_alerts(reading_dict: dict) -> dict:
    """
    Evaluate equipment readings and generate alerts
    
    Returns:
        {
            'critical': list of critical alerts,
            'warning': list of warning alerts,
            'all': list of all alerts (critical + warning)
        }
    """
    critical = []
    warning = []
    
    # Critical: Fault code
    fault_code = reading_dict.get('fault_code')
    if fault_code and fault_code.upper() != 'NONE' and fault_code != '':
        critical.append({
            'code': fault_code,
            'message': f'Unit fault: {fault_code}',
            'severity': 'critical'
        })
    
    # Critical: Abnormal pressures
    discharge_psi = reading_dict.get('discharge_psi')
    suction_psi = reading_dict.get('suction_psi')
    
    if discharge_psi and suction_psi:
        try:
            disch = float(discharge_psi)
            suct = float(suction_psi)
            
            if disch > 350:
                critical.append({
                    'code': 'HIGH_DISCHARGE_PSI',
                    'message': f'High discharge pressure: {disch} PSI',
                    'severity': 'critical'
                })
            
            if suct < 0 or suct > 150:
                critical.append({
                    'code': 'ABNORMAL_SUCTION_PSI',
                    'message': f'Abnormal suction pressure: {suct} PSI',
                    'severity': 'critical'
                })
        except (ValueError, TypeError):
            pass
    
    # Warning: Low Delta-T
    delta_t = reading_dict.get('delta_t')
    if delta_t:
        try:
            delta = float(delta_t)
            if 0 < delta < 14:
                warning.append({
                    'code': 'LOW_DELTA_T',
                    'message': f'Low Delta-T: {delta}°F (possible refrigerant leak)',
                    'severity': 'warning'
                })
        except (ValueError, TypeError):
            pass
    
    # Warning: Voltage imbalance
    v_1 = reading_dict.get('v_1')
    v_2 = reading_dict.get('v_2')
    v_3 = reading_dict.get('v_3')
    
    if v_1 and v_2 and v_3:
        try:
            volts = [float(v_1), float(v_2), float(v_3)]
            avg_volts = sum(volts) / 3
            
            max_dev = max(abs(v - avg_volts) for v in volts)
            imbalance = (max_dev / avg_volts * 100) if avg_volts > 0 else 0
            
            if imbalance > 5:
                warning.append({
                    'code': 'VOLTAGE_IMBALANCE',
                    'message': f'Voltage imbalance: {imbalance:.1f}%',
                    'severity': 'warning'
                })
            
            if avg_volts < 400:
                warning.append({
                    'code': 'LOW_VOLTAGE',
                    'message': f'Low average voltage: {avg_volts:.0f}V',
                    'severity': 'warning'
                })
        except (ValueError, TypeError):
            pass
    
    # Warning: High compressor amps
    compressor_amps = reading_dict.get('compressor_amps')
    if compressor_amps:
        try:
            amps = float(compressor_amps)
            if amps > 70:
                warning.append({
                    'code': 'HIGH_COMPRESSOR_AMPS',
                    'message': f'High compressor amperage: {amps}A',
                    'severity': 'warning'
                })
        except (ValueError, TypeError):
            pass
    
    # Warning: Extreme temperatures
    supply_temp = reading_dict.get('supply_temp')
    if supply_temp:
        try:
            supply = float(supply_temp)
            if supply < 40 or supply > 70:
                warning.append({
                    'code': 'EXTREME_TEMP',
                    'message': f'Extreme supply temperature: {supply}°F',
                    'severity': 'warning'
                })
        except (ValueError, TypeError):
            pass
    
    all_alerts = critical + warning
    
    return {
        'critical': critical,
        'warning': warning,
        'all': all_alerts
    }
