import numpy
import progressbar

def windowed_least_squares(x, y, width, mask = None):
    """
    For every point x, y fit a line to a window with x within <-width / 2, +width / 2>
    of that point, return slopes of these lines and y positions of the central point
    on these lines.

    If mask is not None, then False values in this array mark items to be skipped.

    Runs in O(n).
    """
    x_sum = 0
    y_sum = 0
    xy_sum = 0
    xx_sum = 0
    right = 0
    left = 0
    count = 0

    slope = numpy.empty_like(x)
    offset = numpy.empty_like(x)

    width /= 2

    bar = progressbar.ProgressBar(maxval = len(x))
    bar.start()

    for i, x0 in enumerate(x):
        bar.update(i)

        while right < len(x):
            if x[right] > x0 + width:
                break;

            if mask is None or not mask[right]:
                x_val = x[right]
                y_val = y[right]

                x_sum += x_val
                y_sum += y_val
                xy_sum += x_val * y_val
                xx_sum += x_val * x_val
                count += 1

            right += 1

        while left < right:
            if x[left] >= x0 - width:
                break

            if mask is None or not mask[left]:
                x_val = x[left]
                y_val = y[left]

                x_sum -= x_val
                y_sum -= y_val
                xy_sum -= x_val * y_val
                xx_sum -= x_val * x_val
                count -= 1

            left += 1

        if count == 0:
            continue
        if count == 1:
            offset[i] = y[i]
        else:
            slope[i] = (xy_sum * count - x_sum * y_sum) / (xx_sum * count - x_sum * x_sum)
            offset[i] = (slope[i] * (x0 * count  - x_sum) + y_sum) / count

    bar.finish()
    return slope, offset

