# All data analysis functions after contours have been found.

import numpy as np





def compute_thinning_diameters(contour_a: np.ndarray, contour_b: np.ndarray, plate_d: int) -> np.ndarray:
    """
    Takes the two contours outlining the filament, and computes the diameter of the filament at each point along the filament only between the plates.
    Parameters:
    contour_a: np.ndarray
        First contour outlining one side of the filament of form [yvals, xvals]
    contour_b: np.ndarray
        Second contour outlining the other side of the filament of form [yvals, xvals]
    plate_d: int
        Diameter of the bottom plate in pixels

    Returns: np.ndarray
        Array of pixel y-values relative to cropped frame and corresponding filament diameter in pixels.
        [[yval1, diameter1]
         [yval2, diameter2]
        ...]
        
        """
    if len(contour_a) == 0 or len(contour_b) == 0:
        # The filament has broken, no contours
        return np.array([[np.nan, np.nan]])
    else:
        diameters = [] # each element in list is [y coordinate, x-distance]
        for i in range(len(contour_a)):
            # compute distance between the x values.
            d = abs(contour_a[i][1] - contour_b[i][1]) 
            diameters.append([contour_a[i][0], d])
        diameters = np.array(diameters)
    
    # filter for only keeping values that are confined between the two plates (no greater diameter than diameter of plate)
    mask = diameters[:, 1] < plate_d

    return diameters[mask]


def compute_min_diameter(diameters: np.ndarray) -> list:
    """
    Takes the diameters along the length of the filament, and returns the y value and diameter corresponding to the minimum diameter. 
    Use this if you want to find the point with the minimum diameter. It works to plot this across frames you have a filament that reliably thins across the frames.
    If the filament has inhomogeneities across its length, then this approach for plotting across frames won't work as well. 

    Parameters:
    diameters: np.ndarray
        Array of pixel y-values relative to cropped frame and corresponding filament diameter in pixels.
        [[yval1, diameter1]
         [yval2, diameter2]
        ...]
    Returns: list
       [y value of break point relative to cropping parameters, minimum diameter in pixels]"""
    # finding value of the minimum diameter
    min_d = np.min(diameters)       
    # finding all y-values with that lowest distance
    mask = diameters[:,1] == min_d
    min_pts = diameters[mask]
    # Assuming the middle point is the one that is the mid_point
    if len(min_pts) > 1:
        break_point = min_pts[int((len(min_pts)/2))][0]
    else:
        # If there is only one minimum value
        break_point = min_pts[0][0]
    return [break_point, min_d] # choosing list so that it is easy to append to a df


def compute_midpoint_diameter(diameters: np.ndarray) -> list:
    """
    Takes the diameters along the length of the filament, and returns the y value and diameter corresponding to the midpoint of the filament . 
    
    Parameters:
    diameters: np.ndarray
        Array of pixel y-values relative to cropped frame and corresponding filament diameter in pixels.
        [[yval1, diameter1]
         [yval2, diameter2]
        ...]  

    Returns: list
        [y of center point, associated diameter in pixels]
        """
    # Finding center point
    mid_y = int(len(diameters))/2
    # return y, diameter of scenter point
    return list(diameters[mid_y])


