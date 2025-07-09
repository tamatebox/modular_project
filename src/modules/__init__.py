# src/modules/__init__.py
from .base_module import BaseModule
from .vco import VCO
from .vca import VCA

# from .lfo import LFO
# from .vcf import VCF

__all__ = ["BaseModule", "VCO", "VCA"]
