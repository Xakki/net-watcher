"""Container entrypoint for the mTLS client scaffold.

No default destination or plaintext transport exists. A future client must be
wired to the broker contract explicitly before this profile can run.
"""
from tools.broker_runtime import BrokerRuntimeError


def main() -> int:
    raise BrokerRuntimeError("broker client transport is not configured")


if __name__ == "__main__":
    main()
