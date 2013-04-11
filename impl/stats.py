from __future__ import division, print_function

import collections

try:
    long
except:
    long = int

class Stats:
    """
    Calculate mean, variance and histogram. Fixed point arithmetic is used for all sums.
    """

    def __init__(self, multiplier, hist_resolution = 1):
        self.count = 0
        self.simple_sum = 0
        self.squared_sum = 0
        self.maximum = None

        self.multiplier = multiplier
        self.hist_resolution = hist_resolution

    def add(self, value):
        """
        Add another value.
        """
        self.count += 1

        self.maximum = max(self.maximum, value)

        value = value * self.multiplier

        self.simple_sum += long(value)
        self.squared_sum += long(value * value)

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
