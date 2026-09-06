"""Container entrypoint for the broker profile.

The production verifier and transport are intentionally not implemented in this
scaffold. Refusing here prevents accidental plaintext or unsigned operation.
"""
from tools.broker_runtime import (
    BrokerRuntimeError,
    RealSecretFiles as SafeSecretFiles,
    RuntimeConfig,
    preflight,
)


class RealSecretFiles(SafeSecretFiles):
    """Entrypoint adapter for descriptor-bound secret access."""


class UnavailableVerifier:
    def __init__(self, material: bytes):
        raise BrokerRuntimeError("no production approval verifier is configured")


def main() -> int:
    config = RuntimeConfig.from_env()
    preflight(config, RealSecretFiles(), None, None, UnavailableVerifier)
    return 0


if __name__ == "__main__":
    main()
