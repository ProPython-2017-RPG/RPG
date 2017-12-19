from setuptools import setup, find_packages
import RPG

setup(
    name='RPG',
    version=RPG.__version__,
    packages=find_packages(),
    include_package_data=True,
    author='Bread_Company',
    description='This is RPG game',
    install_requires=[
        'Pygame',
        'Pyganim'
    ]
)
