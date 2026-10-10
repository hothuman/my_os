"""Memory helpers for StudentOS."""
from __future__ import annotations

from .kernel import kernel_instance


def get_used_memory() -> int:
    """Return used memory."""
    return kernel_instance.memory_info()["used"]


def get_free_memory() -> int:
    """Return free memory."""
    return kernel_instance.memory_info()["free"]


def allocate_memory(size: int) -> int:
    """Allocate memory and return used amount, or -1 on failure."""
    if kernel_instance.allocate_memory(int(size)):
        return kernel_instance.memory_info()["used"]
    return -1


def free_memory(size: int) -> int:
    """Free memory and return used amount."""
    kernel_instance.free_memory(int(size))
    return kernel_instance.memory_info()["used"]
