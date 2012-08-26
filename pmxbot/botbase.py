# temporary for backward compatibility
from .core import *

import warnings
warnings.warn("botbase is deprecated. Use `pmxbot.core` instead",
	DeprecationWarning)
