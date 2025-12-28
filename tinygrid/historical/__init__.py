"""Historical data access for tinygrid.

Note: ERCOTArchive has been moved to tinygrid.ercot.archive.
This module is kept for backward compatibility.
"""

from ..ercot.archive import ArchiveLink, ERCOTArchive

__all__ = ["ArchiveLink", "ERCOTArchive"]
