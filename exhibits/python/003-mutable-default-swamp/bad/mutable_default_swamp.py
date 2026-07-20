"""Accident scene: state deposited in a mutable default argument."""


def collect_task(task: str, tasks: list[str] = []) -> list[str]:
    """Add a task to what callers mistakenly believe is a fresh list."""
    tasks.append(task)
    return list(tasks)


def demonstrate() -> str:
    first_visit = collect_task("inspect-volcano")
    second_visit = collect_task("repair-bridge")
    contaminated = "yes" if "inspect-volcano" in second_visit else "no"
    return (
        f"first={','.join(first_visit)}|"
        f"second={','.join(second_visit)}|"
        f"contaminated={contaminated}"
    )


if __name__ == "__main__":
    print(demonstrate())
