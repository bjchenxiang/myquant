import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors
from matplotlib.colors import LogNorm
import numpy as np

def t1():
    x, y = np.random.rand(10), np.random.rand(10)
    z = (np.random.rand(9000000)+np.linspace(0,1, 9000000)).reshape(3000, 3000)
    plt.imshow(z+10, extent=(np.amin(x), np.amax(x), np.amin(y), np.amax(y)),
        cmap=cm.hot, norm=LogNorm())
    plt.colorbar()
    plt.show()

def t2():
    x,y,c = zip(*np.random.rand(30,3)*4-2)

    norm=plt.Normalize(-2,2)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["red","violet","blue"])

    plt.scatter(x,y,c=c, cmap=cmap, norm=norm)
    plt.colorbar()
    plt.show()

if __name__ == '__main__':
    t2()