import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def hex_to_rgb(hex: str) -> tuple:
    """Converts a hex color string to a tuple of RGB values."""
    hex = hex.lstrip("#")
    return tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    """Converts a tuple of RGB values to a hex color string."""
    return "#%02x%02x%02x" % rgb


def rgb_to_brightness(rgb: tuple[float, float, float]) -> float:
    """Converts a tuple of RGB values to a brightness value."""
    return np.sqrt(
        0.299 * rgb[0] ** 2 + 0.587 * rgb[1] ** 2 + 0.114 * rgb[2] ** 2
    )


def hex_to_brightness(hex: str) -> float:
    """Converts a hex color string to a brightness value."""
    return rgb_to_brightness(hex_to_rgb(hex))
