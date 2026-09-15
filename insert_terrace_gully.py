"""Insert terrace and gully_plug design functions into watershed calculator."""
import os

os.chdir(r'D:\eco_nojin')
filepath = 'engine/hydroma/watershed/calculator.py'
with open(filepath, 'r') as f:
    content = f.read()

insert_point = content.find('def design_watershed_structure(')

new_functions = '''
def design_terrace(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
    terrace_width_m: float = 2.0,
) -> dict:
    """Design bench terraces for slope reduction and erosion control."""
    if area_m2 <= 0:
        raise ValueError(f'Area must be positive, got {area_m2}')
    if slope_pct < 0:
        raise ValueError(f'Slope must be non-negative, got {slope_pct}')

    if slope_pct > 30:
        spacing_m = 15
    elif slope_pct > 15:
        spacing_m = 25
    elif slope_pct > 8:
        spacing_m = 35
    else:
        spacing_m = 50

    field_side = math.sqrt(area_m2)
    n_rows = max(1, math.ceil(field_side / spacing_m))
    total_length = n_rows * field_side

    channel_depth = 0.3
    channel_volume_per_m = 0.135
    total_volume = total_length * channel_volume_per_m

    erosion_reduction_pct = min(90, round((1 - spacing_m / field_side) * 70))
    cost = total_length * 12

    return {
        'structure_type': 'terrace',
        'n_rows': n_rows,
        'spacing_m': round(spacing_m, 1),
        'total_length_m': round(total_length, 0),
        'channel_depth_m': round(channel_depth, 2),
        'channel_volume_m3': round(total_volume, 1),
        'erosion_reduction_pct': erosion_reduction_pct,
        'estimated_cost_usd': round(cost, 0),
        'materials': ['excavated_soil', 'stone_outlet'],
    }


def design_gully_plug(
    slope_pct: float,
    area_m2: float,
    rainfall_mm: float = 100,
    gully_width_m: float = 2.0,
) -> dict:
    """Design gully plugs for ephemeral gully control."""
    if area_m2 <= 0:
        raise ValueError(f'Area must be positive, got {area_m2}')
    if gully_width_m <= 0:
        raise ValueError(f'Gully width must be positive, got {gully_width_m}')

    runoff_m3 = calculate_runoff(area_m2, rainfall_mm, runoff_coefficient=0.7)
    plug_height = min(1.5, max(0.3, gully_width_m * 0.3))

    if slope_pct > 20:
        plug_spacing = 20
    elif slope_pct > 10:
        plug_spacing = 40
    else:
        plug_spacing = 60

    gully_length = math.sqrt(area_m2)
    n_plugs = max(1, math.ceil(gully_length / plug_spacing))

    top_width = gully_width_m
    bottom_width = plug_height * 1.5
    volume_per_plug = (top_width + bottom_width) / 2 * plug_height * 1.0
    total_volume = n_plugs * volume_per_plug
    sediment_retention = round(runoff_m3 * 0.3 * n_plugs, 1)
    cost = total_volume * 60

    return {
        'structure_type': 'gully_plug',
        'n_plugs': n_plugs,
        'plug_spacing_m': round(plug_spacing, 1),
        'plug_height_m': round(plug_height, 2),
        'gully_width_m': round(gully_width_m, 2),
        'total_volume_m3': round(total_volume, 1),
        'sediment_retention_m3': sediment_retention,
        'runoff_volume_m3': round(runoff_m3, 1),
        'estimated_cost_usd': round(cost, 0),
        'materials': ['stone', 'gabion', 'excavated_soil'],
    }


'''

content = content[:insert_point] + new_functions + content[insert_point:]

with open(filepath, 'w') as f:
    f.write(content)

print('Done - inserted terrace and gully_plug functions')