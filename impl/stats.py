import collections

class Stats:
    """
    Calculate mean, variance and histogram. Fixed point arithmetic is used for all sums.
    """

    def __init__(self, multiplier, hist_resolution):
        self.histogram = collections.Counter()
        self.count = 0
        self.simple_sum = 0
        self.squared_sum = 0

        self.multiplier = multiplier
        self.hist_resolution = hist_resolution

    def add(self, value):
        """
        Add another value.
        """
        self.histogram[value // self.hist_resolution] += 1
        self.count += 1

        value = value * self.multiplier

        self.simple_sum += int(value)
        self.squared_sum += int(value * value)

    def mean(self):
        """
        Return mean of the values so far.
        """
        return (self.simple_sum / self.count) / self.multiplier

    def variance(self):
        """
        Return variance of the values so far.
        """
        return ((self.squared_sum - self.simple_sum * self.simple_sum / self.count) /
            (self.count - 1)) / (self.multiplier * self.multiplier)

    def print_histogram(self, f):
        """
        Print histogram to a file.
        """
        for i in sorted(self.histogram):
            print(i * self.hist_resolution, self.histogram[i], file=f)
        
