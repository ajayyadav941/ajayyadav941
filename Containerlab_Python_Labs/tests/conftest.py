import os

import pytest
from netmiko import ConnectHandler


LAB_USERNAME = os.getenv("LAB_USERNAME", "root")
LAB_PASSWORD = os.getenv("LAB_PASSWORD")


def _device(host):
    if not LAB_PASSWORD:
        raise RuntimeError(
            "LAB_PASSWORD is not set. Build the FRR image with the same password "
            "and export LAB_PASSWORD before running pytest."
        )
    return {
        "device_type": "linux",
        "host": host,
        "username": LAB_USERNAME,
        "password": LAB_PASSWORD,
    }


R1 = _device("172.20.20.11")
R2 = _device("172.20.20.12")


@pytest.fixture(scope="session")
def r1_connection():
    print("\nConnecting to R1...")
    connection = ConnectHandler(**R1)
    yield connection
    print("\nDisconnecting from R1...")
    connection.disconnect()


@pytest.fixture(scope="session")
def r2_connection():
    print("\nConnecting to R2...")
    connection = ConnectHandler(**R2)
    yield connection
    print("\nDisconnecting from R2...")
    connection.disconnect()
