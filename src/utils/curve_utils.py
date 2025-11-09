import numpy as np

def catmull_rom_spline(points, num_segments=5):
    """
    Generates a smooth curve using Catmull-Rom spline interpolation.
    Points should be a list of [x, y] coordinates.
    """
    if len(points) < 2:
        return points
    if len(points) == 2:
        # For two points, just generate intermediate points linearly
        p1 = np.array(points[0])
        p2 = np.array(points[1])
        return [list(p1 + (p2 - p1) * t) for t in np.linspace(0, 1, num_segments)]

    # Add virtual start and end points for the spline to pass through the actual endpoints
    p = [points[0]] + points + [points[-1]]
    p = np.array(p)
    
    curve_points = []
    for i in range(1, len(p) - 2):
        for t in np.linspace(0, 1, num_segments, endpoint=False):
            # Catmull-Rom spline formula
            h1 = 2 * t**3 - 3 * t**2 + 1
            h2 = -2 * t**3 + 3 * t**2
            h3 = t**3 - 2 * t**2 + t
            h4 = t**3 - t**2

            point = (h1 * p[i] + h2 * p[i+1] + h3 * (p[i+1] - p[i-1]) / 2 + h4 * (p[i+2] - p[i]) / 2)
            curve_points.append(list(point))
    
    # Add the last actual point
    curve_points.append(list(points[-1]))
    return curve_points
