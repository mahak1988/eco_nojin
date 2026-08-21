"""
Soil Recommendations Engine.

Generates comprehensive soil management recommendations.

References:
    [1] Brady, N.C. and Weil, R.R., "The Nature and Properties of Soils", 2017
    [2] USDA NRCS, "Soil Health Management", 2023
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def generate_recommendations(soil_data: Dict) -> Dict:
    """Generate comprehensive soil management recommendations.
    
    Args:
        soil_data: Dictionary containing soil analysis results
        
    Returns:
        Dict: Comprehensive recommendations
    """
    recommendations = {
        'generated_at': datetime.utcnow().isoformat(),
        'priority_actions': [],
        'fertility_management': [],
        'physical_management': [],
        'biological_management': [],
        'monitoring_plan': [],
        'estimated_costs': {}
    }
    
    # Extract relevant data
    health_score = soil_data.get('health_score', 50)
    ph = soil_data.get('ph', 6.5)
    organic_matter = soil_data.get('organic_matter', 2.0)
    texture = soil_data.get('texture', 'loam')
    salinity = soil_data.get('salinity', {})
    
    # Priority actions based on health score
    if health_score < 40:
        recommendations['priority_actions'].append({
            'action': 'immediate_remediation',
            'urgency': 'high',
            'description': 'Soil health is critically low, immediate action needed'
        })
    elif health_score < 60:
        recommendations['priority_actions'].append({
            'action': 'improvement_plan',
            'urgency': 'medium',
            'description': 'Soil health needs improvement'
        })
    else:
        recommendations['priority_actions'].append({
            'action': 'maintenance',
            'urgency': 'low',
            'description': 'Maintain current soil health'
        })
    
    # pH management
    if ph < 6.0:
        recommendations['fertility_management'].append({
            'issue': 'acidic_soil',
            'action': 'apply_lime',
            'details': f'Current pH {ph}, target 6.5',
            'estimated_cost': '$50-100/ha'
        })
    elif ph > 7.5:
        recommendations['fertility_management'].append({
            'issue': 'alkaline_soil',
            'action': 'apply_sulfur',
            'details': f'Current pH {ph}, target 7.0',
            'estimated_cost': '$30-80/ha'
        })
    
    # Organic matter management
    if organic_matter < 2.0:
        recommendations['biological_management'].append({
            'issue': 'low_organic_matter',
            'action': 'add_compost',
            'details': f'Current OM {organic_matter}%, target 2-3%',
            'estimated_cost': '$100-200/ha'
        })
    
    # Texture-specific recommendations
    texture_recommendations = _get_texture_recommendations(texture)
    if texture_recommendations:
        recommendations['physical_management'].extend(texture_recommendations)
    
    # Salinity recommendations
    if salinity.get('classification') not in ['non_saline', None]:
        recommendations['physical_management'].append({
            'issue': 'salinity',
            'action': salinity.get('management', {}).get('action', 'monitor'),
            'details': salinity.get('description', 'Manage salinity')
        })
    
    # Monitoring plan
    recommendations['monitoring_plan'] = _create_monitoring_plan(health_score)
    
    return recommendations


def _get_texture_recommendations(texture: str) -> List[Dict]:
    """Get recommendations based on soil texture."""
    recommendations = []
    
    if texture in ['sand', 'loamy_sand']:
        recommendations.append({
            'issue': 'low_water_holding',
            'action': 'add_organic_matter',
            'details': 'Sandy soils need organic matter to improve water retention',
            'practice': 'Apply 2-5 cm compost annually'
        })
    
    elif texture in ['clay', 'silty_clay']:
        recommendations.append({
            'issue': 'poor_drainage',
            'action': 'improve_structure',
            'details': 'Clay soils need improved drainage and structure',
            'practice': 'Add gypsum and organic matter, consider raised beds'
        })
    
    elif texture == 'silt':
        recommendations.append({
            'issue': 'compaction_risk',
            'action': 'avoid_compaction',
            'details': 'Silty soils are prone to compaction',
            'practice': 'Minimize traffic when wet, add organic matter'
        })
    
    return recommendations


def _create_monitoring_plan(health_score: float) -> List[Dict]:
    """Create monitoring plan based on health score."""
    plan = []
    
    # Basic monitoring
    plan.append({
        'parameter': 'pH',
        'frequency': 'annually',
        'method': 'Soil test'
    })
    
    plan.append({
        'parameter': 'organic_matter',
        'frequency': 'annually',
        'method': 'Soil test'
    })
    
    plan.append({
        'parameter': 'NPK',
        'frequency': 'annually',
        'method': 'Soil test'
    })
    
    # Additional monitoring for poor health
    if health_score < 60:
        plan.append({
            'parameter': 'EC (salinity)',
            'frequency': 'semi-annually',
            'method': 'EC meter'
        })
        
        plan.append({
            'parameter': 'Soil structure',
            'frequency': 'quarterly',
            'method': 'Visual assessment'
        })
    
    # Biological monitoring
    plan.append({
        'parameter': 'Earthworm count',
        'frequency': 'annually',
        'method': 'Visual count'
    })
    
    return plan


def estimate_amendment_costs(recommendations: Dict) -> Dict:
    """Estimate total costs for recommended amendments."""
    total_min = 0
    total_max = 0
    
    cost_ranges = {
        'apply_lime': (50, 100),
        'apply_sulfur': (30, 80),
        'add_compost': (100, 200),
        'apply_gypsum': (40, 120),
        'install_drainage': (200, 500),
    }
    
    for category in ['fertility_management', 'physical_management', 'biological_management']:
        for rec in recommendations.get(category, []):
            action = rec.get('action', '')
            if action in cost_ranges:
                min_cost, max_cost = cost_ranges[action]
                total_min += min_cost
                total_max += max_cost
    
    return {
        'estimated_min': total_min,
        'estimated_max': total_max,
        'unit': '$/ha',
        'interpretation': f'Total estimated cost: ${total_min}-${total_max}/ha'
    }
