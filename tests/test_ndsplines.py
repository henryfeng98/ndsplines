import pytest
import ndsplines
import numpy as np
from numpy.testing import assert_almost_equal
import itertools

np.random.seed(0)

#
# Integration/Miscellaneous tests
#

def test_evaluate_spline_different_impls():
    """Check that setting the backend implementation is effective."""
    ndsplines.set_impl('numpy')
    f_numpy = ndsplines.evaluate_spline

    ndsplines.set_impl('cython')
    f_cython = ndsplines.evaluate_spline

    assert f_numpy is not f_cython


#
# Scipy compatibility tests
#

def test_make_interp_scipy_compat():
    """Basic test of compatibility with scipy.interpolate API."""
    x = np.linspace(0, 1, 10)
    y = np.sin(x)
    spl = ndsplines.make_interp_spline(x, y)
    spl(np.linspace(0, 1, 100))


# Input/output API tests

def test_make_interp_invalid_x():
    """Bad input raises ValueError."""
    with pytest.raises(ValueError):
        ndsplines.make_interp_spline('str', np.arange(3))


def test_make_interp_invalid_y():
    """Bad input raises ValueError."""
    with pytest.raises(ValueError):
        ndsplines.make_interp_spline(np.arange(10), np.zeros((9, 10, 10, 10)))


@pytest.mark.parametrize('n_vals', [[8, 16], [8, 10, 12]])
def test_make_interp_x_vectors(n_vals):
    """Check that a list of vectors is accepted for x.

    y input in this case should have shape (n_ndim1, n_ndim2, ...) as if it
    were sampled on the grid.
    """
    x = [np.linspace(0, 1, n) for n in n_vals]
    xgrid = np.stack(np.meshgrid(*x, indexing='ij'), axis=-1)
    y = np.random.rand(*n_vals)

    spl = ndsplines.make_interp_spline(x, y)

    assert spl.xdim == len(n_vals)
    assert spl.ydim == 1
    assert_almost_equal(spl(xgrid), y)


@pytest.mark.parametrize('n_vals', [[10], [10, 12], [10, 12, 15]])
def test_make_interp_x_mesh(n_vals):
    """Input x arrays of varying dimensionality."""
    xarrays = [np.linspace(0, 1, n) for n in n_vals]
    x = np.stack(np.meshgrid(*xarrays, indexing='ij'), axis=-1)
    y = np.random.rand(*n_vals)

    spl = ndsplines.make_interp_spline(x, y)
    assert spl.xdim == len(n_vals)

    xsamp = np.random.randn(10, len(n_vals))
    assert spl(xsamp).shape == (10,)


@pytest.mark.parametrize('ydim', [2, 3])
def test_make_interp_nd_y(ydim):
    """Multi-dimensional y."""
    x = np.linspace(0, 1, 10)
    y = np.random.rand(10, ydim)

    spl = ndsplines.make_interp_spline(x, y)

    assert spl.xdim == 1
    assert spl.ydim == ydim

    samps = spl(np.random.rand(20))
    assert samps.shape == (20, ydim)


def test_make_interp_1d_y():
    """Check that output is squeezed ndim==1 for 1D y."""
    x = np.linspace(0, 1, 10)
    y = np.sin(x)
    spl = ndsplines.make_interp_spline(x, y)
    assert spl(np.random.rand(20)).shape == (20,)


#
# Mathematical tests
#

def test_make_interp_nn():
    """Verify nearest neighbor special case."""
    dx = 0.1
    x = np.arange(0, 1, dx)
    y = np.sin(2*np.pi*x)

    spl = ndsplines.make_interp_spline(x, y, bcs=[(0, 0), (0, 0)], degrees=0)

    # samples at offsets less than dx/2 will be same as original values
    xx = x[:-1] + dx/4
    assert_almost_equal(spl(xx), spl(x[:-1]))
