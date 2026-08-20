import docker


def list_containers() -> str:
    """
    List all Docker containers on the server.

    Returns each container's:
    - name
    - status
    - image
    - health status

    This tool is read-only.
    """

    client = docker.from_env()
    containers = client.containers.list(all=True)

    if not containers:
        return "No Docker containers found."

    results = []

    for container in containers:
        state = container.attrs.get("State", {})

        health = state.get("Health", {}).get("Status", "no-healthcheck")

        image = container.attrs.get("Config", {}).get("Image", "unknown")

        results.append(
            f"Name: {container.name}\n"
            f"Status: {container.status}\n"
            f"Health: {health}\n"
            f"Image: {image}\n"
        )

    return "\n".join(results)


def get_container_logs(
    container_name: str,
    tail: int = 100,
) -> str:
    """
    Return recent logs from a Docker container.

    Args:
        container_name:
            Name or ID of the Docker container.

        tail:
            Number of recent log lines to return.

    This tool is read-only.
    """

    client = docker.from_env()

    try:
        container = client.containers.get(container_name)

        logs = container.logs(
            tail=tail,
            timestamps=True,
        )

        decoded_logs = logs.decode(
            "utf-8",
            errors="replace",
        )

        if not decoded_logs.strip():
            return f"Container '{container_name}' " "returned no recent logs."

        return decoded_logs

    except docker.errors.NotFound:
        return f"ERROR: Docker container " f"'{container_name}' was not found."

    except Exception as exc:
        return f"ERROR reading logs from " f"'{container_name}': {exc}"
