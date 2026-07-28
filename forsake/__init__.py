"""
Forsake — GoPhish + NGINX Superpower Phishing Engagement Toolkit
Created by ANONYMOUS-BETA
https://github.com/anonymous-beta/Forsake

Authorized penetration testing use only.
"""

__version__ = "2.0.0"
__author__ = "ANONYMOUS-BETA"
__description__ = "Enterprise-grade phishing engagement platform combining GoPhish with hardened NGINX proxy"

from .core import Forsake
from .gophish_module import GoPhishManager
from .nginx_module import NginxManager
from .ssl_module import CertManager
from .clone_module import LandingPageCloner
