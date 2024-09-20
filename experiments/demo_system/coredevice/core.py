import typing
import logging

import artiq.coredevice.core

__all__ = ['Core']

_logger: logging.Logger = logging.getLogger(__name__)
"""The logger for this file."""

_unit_to_bytes: typing.Dict[str, int] = {
    'b': 1000 ** 0,
    'kb': 1000 ** 1,
    'mb': 1000 ** 2,
    'gb': 1000 ** 3,
    'kib': 1024 ** 1,
    'mib': 1024 ** 2,
    'gib': 1024 ** 3,
}
"""Dict to map a string data size unit to bytes."""


def _str_to_bytes(string: typing.Optional[str]) -> typing.Optional[int]:
    """Convert a string to bytes."""
    assert isinstance(string, str) or string is None, 'Input must be of type str or None'

    if string:
        # Format string
        string = string.strip().lower()

        try:
            # Extract the unit from the string
            unit_str: str = ''
            for prefix in (string[-i:] for i in [3, 2, 1] if len(string) > i):
                if prefix in _unit_to_bytes:
                    unit_str = prefix
                    break
            # Convert the value and the unit
            unit = _unit_to_bytes[unit_str]  # Do the unit first to fail early
            value = int(string[:-len(unit_str)])
            # Return the product
            return value * unit
        except KeyError:
            raise ValueError(f'No valid data size unit was found at the end of string "{string}"')
        except ValueError:
            raise ValueError(f'No valid integer was found at the start of string "{string}"')
    else:
        # Return None in case the string is None or empty
        return None


class KernelSizeException(Exception):
    """Raised if the maximum kernel size is exceeded."""
    pass


class Core(artiq.coredevice.core.Core):
    """A backwards compatible extension of the standard core driver."""

    def __init__(self, *args: typing.Any, max_kernel_size: typing.Optional[str] = None, **kwargs: typing.Any):
        """Create a new core driver.

        :param args: Positional arguments passed to the core driver
        :param max_kernel_size: Maximum kernel size (e.g. ``"256 MiB"``, ``"512 kB"``)
        :param kwargs: Keyword arguments passed to the core driver
        """
        assert max_kernel_size is None or isinstance(max_kernel_size, str)

        # Store attributes
        self._max_kernel_size: typing.Optional[int] = _str_to_bytes(max_kernel_size)
        assert self._max_kernel_size is None or self._max_kernel_size >= 0

        # Call super
        super(Core, self).__init__(*args, **kwargs)

    def compile(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        # Call super
        _logger.debug('Compiling...')
        embedding_map, kernel_library, symbolizer, demangler = super(Core, self).compile(*args, **kwargs)

        # Obtain kernel size in bytes
        kernel_size: int = len(kernel_library)

        if self._max_kernel_size is None:
            # Report kernel size
            _logger.debug('Kernel size: %d bytes', kernel_size)
        else:
            # Check kernel size
            _logger.debug('Kernel size: %d/%d bytes (%.2f%%)',
                          kernel_size, self._max_kernel_size, kernel_size / self._max_kernel_size)
            if kernel_size > self._max_kernel_size:
                raise KernelSizeException(f'Kernel too large: {kernel_size}/{self._max_kernel_size} bytes')

        # Return values
        return embedding_map, kernel_library, symbolizer, demangler
