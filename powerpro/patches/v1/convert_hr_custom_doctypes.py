"""Convert the scoped HR definitions before standard sync and orphan cleanup."""
from powerpro.custom_hr.installer import install


def execute():
    install()
