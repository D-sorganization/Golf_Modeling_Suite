# sharedthon.core

Core lightweight utilities for the Golf Modeling Suite.

This module contains base exceptions and logging setup that do not require
heavy dependencies like numpy, pandas, or matplotlib.

## Classes

### GolfModelingError

Base exception for golf modeling suite.

**Inherits from:** Exception

### EngineNotFoundError

Raised when a physics engine is not found or not properly installed.

**Inherits from:** GolfModelingError

### DataFormatError

Raised when data format is invalid or unsupported.

**Inherits from:** GolfModelingError
