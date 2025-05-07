from setuptools import setup, find_packages

setup(
    name="ip_checker",
    version="1.5",
    packages=find_packages(),
    install_requires=[
        "geoip2>=4.7.0",
        "pandas>=2.1.0",
        "openpyxl>=3.1.2",
        "termcolor>=2.3.0",
        "ipaddress>=1.0.23",
    ],
    entry_points={
        'console_scripts': [
            'ip-checker=ip_checker.main:main',
        ],
    },
    author="Nicolas Saputra Gunawan",
    python_requires=">=3.8",
)
