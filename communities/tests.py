"""
Deprecated test module. Tests have been moved into the
`communities.tests` package for better organization.

Importing the package here prevents older test discovery from
finding duplicate tests; no tests are defined in this module.
"""

from . import tests  # keep import for backward compatibility
