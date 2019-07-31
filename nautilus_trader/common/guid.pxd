# -------------------------------------------------------------------------------------------------
# <copyright file="guid.pxd" company="Nautech Systems Pty Ltd">
#  Copyright (C) 2015-2019 Nautech Systems Pty Ltd. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  https://nautechsystems.io
# </copyright>
# -------------------------------------------------------------------------------------------------

from nautilus_trader.core.types cimport GUID


cdef class GuidFactory:
    """
    The abstract base class for all GUID factories.
    """

    cpdef GUID generate(self)


cdef class TestGuidFactory(GuidFactory):
    """
    Provides a fake GUID factory for testing purposes.
    """
    cdef GUID _guid



cdef class LiveGuidFactory(GuidFactory):
    """
    Provides a GUID factory for live trading. Generates actual GUIDs based on
    Pythons UUID4.
    """
    pass
