from __future__ import division

import urllib2
import urlparse
import logging
import subprocess
import UserDict
import numpy

import warnings
warnings.simplefilter('ignore', numpy.RankWarning)

class Ephemeris(object):
    def sv_pos(self, prn, week, time):
        raise NotImplementedError()

    def sv_clock_offset(self, prn, week, time):
        raise NotImplementedError()

    def sv_velocity(self, prn, week, time):
        raise NotImplementedError()

    def sv_clock_drift(self, prn, week, time):
        raise NotImplementedError()

class IGSEphemeris(Ephemeris):
    """
    Download precise ephemeris from igs.
    This is intended for real time applications --
    always uses the predicted ultra rapid solutions, even
    when more complete dataset is available.
    """
    def __init__(self, server):
        self._server = server
        self._validity_interval = _EmptyInterval()
        self._loaded_interval = _EmptyInterval()
        self._week = None
        self._polynomials = {}

    def _ensure_valid(self, week, time):
        """
        If the time isn't in validity interval,
        then download and parse a new sp3 file.
        """
        if time in self._validity_interval and self._week == week:
            return

        rounded_time_2 = (time // (2 * 3600)) * (2 * 3600)
        rounded_time_6 = (time // (6 * 3600)) * (6 * 3600)
        
        file_name = self._get_file_name(week, time)
        remote_file = urlparse.urljoin(self._server, file_name)

        if time not in self._loaded_interval:
            logging.info("Downloading file %s", remote_file)
            f = urllib2.urlopen(remote_file)
            with _decompress_Z_file(f) as f2:
                self._sp3 = Sp3(f2)
            self._loaded_interval = _Interval(rounded_time_6, rounded_time_6 + 6 * 3600)

        logging.info("Recalculating polynomials")
        # find start index for the new validity interval in sp3 file
        start = 0
        for i, epoch in enumerate(self._sp3.values):
            if epoch.time >= rounded_time_2:
                start = i
                break

        epochs = self._sp3.values[start - 8: start + 17]
        for sv in self._sp3.svs:
            if sv[0] != 'G':
                continue # only gps
            prn = int(sv[1:])

            times = numpy.fromiter(
                (x.time for x in epochs),
                dtype=numpy.float)
            positions = []
            for i in range(4):
                values = numpy.fromiter(
                    (x[sv][i] for x in epochs if sv in x),
                    dtype=numpy.float)
                assert len(times) == len(values) == 25
                if i == 4:
                    multiplier = 1e-6
                else:
                    multiplier = 1e3

                #poly = numpy.polynomials.polynomials.Polynomial()
                positions.append(numpy.polyfit(times, values, 12) * multiplier)

            self._positions[prn] = polynomials

        self._validity_interval = _Interval(rounded_time_2, rounded_time_2 + 2 * 3600)
        self._week = week

    def _get_file_name(self, week, time):
        d, rest = divmod(time, 24 * 3600)
        h = rest // 3600

        h = (h // 6) * 6

        return "{w:04}/igu{w:04}{d:01}_{h:02}.sp3.Z".format(
            w=int(week), d=int(d), h=int(h))

    def sv_pos(self, prn, week, time):
        self._ensure_valid(week, time)
        return numpy.matrix([[
            numpy.polyval(self._polynomials[prn][i], time) for i in range(3)]])

    def sv_clock_offset(self, prn, week, time):
        self._ensure_valid(week, time)
        return numpy.polyval(self._polynomials[prn][3], time)

    def sv_velocity(prn, week, time):
        self._ensure_valid(week, time)
        return numpy.matrix([[
            numpy.polyval(self._polynomials[prn][i], time) for i in range(3)]])

    def sv_clock_drift(self, prn, week, time):
        self._ensure_valid(week, time)
        raise NotImplementedError()

class _EmptyInterval:
    def __contains__(self, x):
        return False

    def __str__(self):
        return "Epty interval"

class _Interval:
    def __init__(self, a, b):
        self._a = a
        self._b = b

    def __contains__(self, x):
        return self._a <= x <= self._b

    def __str__(self):
        return "<{}, {}>".format(self._a, self._b)

class Sp3(object):
    """
    Minimalistic parser for sp3 files.
    """

    def __init__(self, f):
        for i in range(14):
            next(f)

        next(f) # ignoring standard deviations

        for i in range(7):
            next(f)

        # now the actual records start
        self.values = []
        self.svs = set()

        for line in f:
            if line == 'EOF':
                break
            elif line[0] == '*':
                self.values.append(UserDict.UserDict())
                week, time = _ymdhm2gps(*map(int, line[1:].strip().split()[:-1]))
                self.values[-1].time = time
            elif line[0] == 'P':
                sv = line[1:4]
                self.values[-1][sv] = map(float, line[4:].strip().split()[:4])
                self.svs.add(sv)
            else:
                pass # we don't process velocities or covariances


def _get_mjd(y, m, d):
    """
    Return modified julian day.
    Taken from http://www.leapsecond.com/tools/gpsdate.c
    """
    return (
        367 * y
        - 7 * (y + (m + 9) // 12) // 4
        - 3 * ((y + (m - 9) // 7) // 100 + 1) // 4
        + 275 * m // 9
        + d
        + 1721028
        - 2400000);

def _ymdhm2gps(y, month, d, h, m):
    """
    Return the gps time without separated 
    week / seconds (the way sirf uses it).
    """
    days = _get_mjd(y, month, d) - _get_mjd(1980, 1, 6)

    week, day = divmod(days, 7)

    return week, (60 * (m + 60 * (h + 24 * day)))
    
def _decompress_Z_file(fileobj):
    """
    Helper function that decompresses the compress'd files (*.Z)
    using an external program.
    This is ugly and not portable.
    """
    gunzip = subprocess.Popen('gunzip', stdin=fileobj, stdout=subprocess.PIPE, shell=True)
    return gunzip.stdout
    
