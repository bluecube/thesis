import numpy
import progressbar

range = xrange

def windowed_least_squares(x, y, width, degree, mask = None):
    """
    For every point x, y fit a polynomial to a window with x within <-width / 2, +width / 2>
    of that point, return slopes of these lines and y positions of the central point
    on these lines.

    If mask is not None, then False values in this array mark items to be skipped.

    Runs in O(n).
    """

    # http://www.personal.psu.edu/jhm/f90/lectures/lsq2.html

    right = 0
    left = 0

    slope = numpy.empty_like(x)
    offset = numpy.empty_like(x)

    width /= 2

    bar = progressbar.ProgressBar(maxval = len(x))

    x_sums = [0] * (2 * degree + 1) # x_sums[i] = sum(x[j]^i for j in window)
    y_sums = [0] * (degree + 1) # y_sums[i] = sum(y[j] * x[j]^i for j in window)

    a = numpy.zeros((degree + 1, degree + 1))

    for i, x0 in bar(enumerate(x)):

        while right < len(x):
            if x[right] > x0 + width:
                break;

            if mask is None or mask[right]:
                x_val = x[right]
                y_val = y[right]

                tmp = 1
                for j in range(degree + 1):
                    x_sums[j] += tmp
                    y_sums[j] += tmp * y_val
                    tmp *= x_val
                for j in range(degree + 1, 2 * degree + 1):
                    x_sums[j] += tmp
                    tmp *= x_val

            right += 1

        while left < right:
            if x[left] >= x0 - width:
                break

            if mask is None or mask[left]:
                x_val = x[left]
                y_val = y[left]

                tmp = 1
                for j in range(degree + 1):
                    x_sums[j] -= tmp
                    y_sums[j] -= tmp * y_val
                    tmp *= x_val
                for j in range(degree + 1, 2 * degree + 1):
                    x_sums[j] -= tmp
                    tmp *= x_val

            left += 1

        #print(x_sums[0])

        if x_sums[0] <= degree:
            slope[i] = 0
            offset[i] = 0
            pass
        else:
            ## put a lower degree  curve through the points if we have nothing better.
            #limit = min(x_sums[0], degree + 1)
            limit = degree + 1

            for j in range(limit):
                for k in range(limit):
                    a[j][k] = x_sums[j + k]
            coefs = numpy.linalg.solve(a, y_sums)

            s = 0
            o = 0
            for j in reversed(range(1, limit)):
                o *= x0
                o += coefs[j]
                s *= x0
                s += coefs[j] * j
            o *= x0
            o += coefs[0]

            slope[i] = s
            offset[i] = o

    print(slope)

    return slope, offset

