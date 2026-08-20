from tools.docker_tools import (
    get_container_logs,
    list_containers,
)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_containers",
            "description": (
                "List all Docker containers on the current server, "
                "including their name, runtime status, health status, "
                "and image. Use this whenever actual Docker container "
                "status is required."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_container_logs",
            "description": (
                "Read recent logs from a Docker container. "
                "Use this when a container is restarting, exited, "
                "unhealthy, crashing, or otherwise needs investigation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "container_name": {
                        "type": "string",
                        "description": (
                            "Exact Docker container name or ID."
                        ),
                    },
                    "tail": {
                        "type": "integer",
                        "description": (
                            "Number of recent log lines to return."
                        ),
                        "minimum": 1,
                        "maximum": 500,
                    },
                },
                "required": [
                    "container_name",
                ],
                "additionalProperties": False,
            },
        },
    },
]


TOOL_FUNCTIONS = {
    "list_containers": list_containers,
    "get_container_logs": get_container_logs,
}
