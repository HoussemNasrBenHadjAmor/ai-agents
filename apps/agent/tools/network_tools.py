import socket
import urllib.request
import urllib.error
import subprocess


def resolve_dns(hostname: str) -> str:
    """
    Resolve a hostname to IP addresses.

    Read-only.
    """

    try:
        results = socket.getaddrinfo(
            hostname,
            None,
        )

        addresses = sorted(
            {
                result[4][0]
                for result in results
            }
        )

        if not addresses:
            return f"No addresses found for {hostname}"

        return (
            f"Hostname: {hostname}\n"
            f"Addresses: {', '.join(addresses)}"
        )

    except Exception as exc:
        return (
            f"DNS resolution failed for "
            f"{hostname}: {exc}"
        )


def check_tcp_port(
    host: str,
    port: int,
    timeout: int = 5,
) -> str:
    """
    Test whether a TCP connection can be established.

    Read-only.
    """

    try:

        with socket.create_connection(
            (host, port),
            timeout=timeout,
        ):

            return (
                f"TCP connection successful\n"
                f"Host: {host}\n"
                f"Port: {port}"
            )

    except Exception as exc:

        return (
            f"TCP connection failed\n"
            f"Host: {host}\n"
            f"Port: {port}\n"
            f"Error: {exc}"
        )


def check_http(
    url: str,
    timeout: int = 10,
) -> str:
    """
    Perform a read-only HTTP GET request.

    Returns HTTP status and selected headers.
    """

    try:

        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent":
                "AI-DevOps-Diagnostic-Agent/1.0"
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            return (
                f"URL: {url}\n"
                f"Status: {response.status}\n"
                f"Final URL: {response.url}\n"
                f"Server: "
                f"{response.headers.get('Server')}\n"
                f"Content-Type: "
                f"{response.headers.get('Content-Type')}"
            )

    except urllib.error.HTTPError as exc:

        return (
            f"URL: {url}\n"
            f"HTTP status: {exc.code}\n"
            f"Reason: {exc.reason}"
        )

    except Exception as exc:

        return (
            f"HTTP request failed\n"
            f"URL: {url}\n"
            f"Error: {exc}"
        )


def get_host_network_info() -> str:
    """
    Return basic host network information.

    Read-only.
    """

    commands = [
        ["ip", "addr"],
        ["ip", "route"],
        ["ss", "-ltn"],
    ]

    outputs = []

    for command in commands:

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
            )

            outputs.append(
                f"$ {' '.join(command)}\n"
                f"{result.stdout}"
            )

        except Exception as exc:

            outputs.append(
                f"$ {' '.join(command)}\n"
                f"ERROR: {exc}"
            )

    return "\n".join(outputs)
