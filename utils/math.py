import math as mt

def ratio_array(start, end, ratio):
    value = round(start * (1+ratio), 3)
    if value >= end:
        return [value]
    else:
        return [value] + ratio_array(value, end, ratio)

def floor(value, percise):
    """
    a = floor(4.55555,2)

    a = 4.55
    """
    value = value * (10 ** percise)
    value = mt.floor(value)
    return value/(10**percise)

def cut(value, unit):
    """
    a = floor(4.55555,0.01)

    a = 4.55
    """
    r = 1 / unit
    if r >= 1:
        return round(mt.floor(value * r)*unit,round(mt.log(round(r), 10)))
    else:
        return mt.floor(value * r)*unit

def get_min_space_index(arr,value):
    arr1 = [value - val if value >= val else value+val for val in arr]
    return arr1.index(min(arr1))

