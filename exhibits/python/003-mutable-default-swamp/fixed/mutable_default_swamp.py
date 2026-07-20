"""Repair: create state per call unless sharing is explicitly requested."""


def collect_task(task: str, tasks: list[str] | None = None) -> list[str]:
    """Add a task to a fresh list or to an explicitly supplied shared list."""
    current_tasks = [] if tasks is None else tasks
    current_tasks.append(task)
    return list(current_tasks)


def demonstrate() -> str:
    first_visit = collect_task("inspect-volcano")
    second_visit = collect_task("repair-bridge")
    isolated = "yes" if first_visit == ["inspect-volcano"] and second_visit == ["repair-bridge"] else "no"
    return (
        f"first={','.join(first_visit)}|"
        f"second={','.join(second_visit)}|"
        f"isolated={isolated}"
    )


if __name__ == "__main__":
    print(demonstrate())
