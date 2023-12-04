#! /usr/bin/python3

from scipy.stats import wasserstein_distance
import numpy as np
import math

def get_emd(iops_0, iops_1, lat_0, lat_1):
    """
    Get the earth movers distance of the data points.

     Parameters
    ----------
    iops_0: IOPS data points (x-axis) of the baseline (0% interference)
    iops_1: IOPS data points (x-axis) of the interference line (50% interference)
    lat_0:  Latency data points (y-axis) of the baseline (0% interference)
    lat_1:  Latency data points (y-axis) of the interference line (50% interference)

    Returns
    -------
    emd : float
        The Earth Mover's Distance.
    """
    
    # dist1 = np.column_stack((iops_0, lat_0))
    # dist2 = np.column_stack((iops_1, lat_1))
    # print(dist1)
    # print(np.array(iops_0))
    # dist1 = dit.Distribution(np.array(iops_0), np.array(lat_0))
    # dist2 = dit.Distribution(np.array(iops_1), np.array(lat_1))

    # return earth_movers_distance(dist1, dist2)

    

def get_interference_rms(iops_0, iops_1, lat_0, lat_1, alpha=0.5, beta=0.5):
    """
    Get the earth movers distance of the data points.

    Parameters
    ----------
    iops_0: IOPS data points (x-axis) of the baseline (0% interference)
    iops_1: IOPS data points (x-axis) of the interference line (50% interference)
    lat_0:  Latency data points (y-axis) of the baseline (0% interference)
    lat_1:  Latency data points (y-axis) of the interference line (50% interference)

    Optional
    ----------
    alpha: The alpha coefficient for the weight of IOPS (default: 0.5)
    beta: The beta coefficient for the weight of Latency (default: 0.5)

    Returns
    -------
    rms : float
        The RMS value.
    """

    # print(f"{iops_0} {iops_1} {lat_0} {lat_1}")

    if len(iops_0) != len(iops_1) and len(lat_0) != len(lat_1):
        print("ERROR: Lines have different number of data points.")
        return -1

    if alpha + beta != 1:
        print("ERROR: Alpha and Beta should be equal to 1 in total (100%).")
        return -1

    n = len(iops_0)
    sum = 0

    for i in range(n):
        sum += math.sqrt(alpha * math.pow(((iops_1[i] - iops_0[i]) / iops_0[i]), 2) + beta * math.pow(((lat_1[i] - lat_0[i]) / lat_0[i]), 2))
    return (sum / n)


def get_interference_gpt(iops_0, iops_1, lat_0, lat_1, alpha=0.5, beta=0.5):
    """
    Get the goodput distance of the data points.

    Parameters
    ----------
    iops_0: IOPS data points (x-axis) of the baseline (0% interference)
    iops_1: IOPS data points (x-axis) of the interference line (50% interference)
    lat_0:  Latency data points (y-axis) of the baseline (0% interference)
    lat_1:  Latency data points (y-axis) of the interference line (50% interference)

    Optional
    ----------
    alpha: The alpha coefficient for the weight of IOPS (default: 0.5)
    beta: The beta coefficient for the weight of Latency (default: 0.5)

    Returns
    -------
    gpt : float
        The goodput value.
        Positive result implies interference with a loss in performance (either lower IOPS or LAT, or both)
        0 implies no interference
        Negative result implies interference with a gain in performance (either higher IOPS or LAT, or both)
    """

    if len(iops_0) != len(iops_1) and len(lat_0) != len(lat_1):
        print("ERROR: Lines have different number of data points.")
        return -1

    if alpha + beta != 1:
        print("ERROR: Alpha and Beta should be equal to 1 in total (100%).")
        return -1

    n = len(iops_0)
    sum = 0

    for i in range(n):
        iops_diff = -1 * alpha * ((iops_1[i] - iops_0[i]) / iops_0[i])
        lat_diff = beta * ((lat_1[i] - lat_0[i]) / lat_0[i])
        sum += iops_diff + lat_diff

    return (sum / n)