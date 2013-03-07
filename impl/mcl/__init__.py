import random

class Prediction:
    """Base class for prediction inputs to MCL."""

    def __enter__(self):
        """Allow use of the correction input as a context manager.
        All access to samples by this input is enclosed in its context."""
        return self

    def __exit__(self, *exc_info):
        """Allow use of the correction input as a context manager.
        All access to samples by this input is enclosed in its context."""
        pass

    def predict(self, sample):
        """Return a new prediction (sample).
        Doesn't modify the sample."""
        raise NotImplemeted()


class Correction:
    """Base class for correction inputs to MCL."""

    def __enter__(self):
        """Allow use of the correction input as a context manager.
        All access to samples by this input is enclosed in its context."""
        return self

    def __exit__(self, *exc_info):
        """Allow use of the correction input as a context manager.
        All access to samples by this input is enclosed in its context."""
        pass

    def correct(self, sample):
        """Return probability of this sample.
        Doesn't modify the sample."""
        raise NotImplemeted()


class MCL:
    """A very simple implementation of Monte Carlo Localization."""

    def __init__(self, n, draw_initial_sample):
        """Prepare the MCL class.

        n - number of samples
        draw_initial_sample - a function that returns a random sample
            in an initial configuration."""

        self._samples = []
        for i in range(n):
            sample = draw_initial_sample()
            sample.weight = 1

            self._samples.append(init)
        self._normalization = n

    def predict(self, prediction_input):
        """Perform a prediction phase using the given input."""

        with prediction_input as p:
            for i, s in enumerate(self._samples):
                self._samples[i] = p.predict(s)

    def correct(self, correction_input):
        """Correct the inputs with the given correction input.
        This method may be called multiple times per one cycle (typically
        with different corrections)."""

        self._normalization = 0
        with correction_input as c:
            for i, s in enumerate(self._samples):
                self._samples[i].weight *= c.correct(s)
                self._normalization += self._samples[i].weight

    def resample(self):
        """Perform the resampling step, finalizing the cycle."""

        avg_weight = self._normalization / self._n

        new_samples = []
        u = random.uniform(0, avg_weight)
        samples_it = iter(self._samples)

        for j in range(self._n):
            while u > 0:
                sample = next(samples)
                u -= sample->weight
            u += avg_weight
            sample.weight = 1
            new_samples.append(sample)

        assert len(new_samples) == self._n
        self._normalization = self._n
