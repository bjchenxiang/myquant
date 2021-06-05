
def ratio_array(start, end, ratio):
    value = round(start * (1+ratio), 3)
    if value >= end:
        return [value]
    else:
        return [value] + ratio_array(value, end, ratio)
