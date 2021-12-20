"""Samplers for probability distributions."""


from math import isclose

from vose_sampler import VoseAlias
from numpy.random import gamma


class FixedSampler:
    """A sampler that returns the same fixed value."""

    def __init__(self, val):
        """Initialize."""
        self.val = val

    def sample(self):
        """Return a sample from the distribution."""
        return self.val


class CategoricalSampler(VoseAlias):
    """A sampler that returns a value from a categorical distribution."""

    def __init__(self, dist):
        """Initialize."""
        if not isclose(sum(dist.values()), 1.0):
            raise ValueError("Probabilities in the distribution dont add up to 1")

        super().__init__(dist)

    def sample(self):
        """Return a sample from the distribution."""
        return self.alias_generation()

class GammaDistributionSampler:
    """A sampler that returns a value from a gamma distribution"""

    def __init__(self, shape, scale):
        self.shape = shape
        self.scale = scale

    def sample(self):
        return round(gamma(self.shape, self.scale))
