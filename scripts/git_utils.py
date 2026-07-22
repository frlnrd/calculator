import subprocess

def checkout_branch(branch_name):

    subprocess.run(
        [
            "git",
            "fetch",
            "origin",
            branch_name
        ],
        check=True
    )

    subprocess.run(
        [
            "git",
            "checkout",
            "-B",
            branch_name,
            f"origin/{branch_name}"
        ],
        check=True
    )

    print("=== CURRENT BRANCH ===")

    subprocess.run(
        ["git", "branch", "--show-current"],
        check=False
    )

    print(f"=== CHECKOUT {branch_name} ===")

def commit_changes(issue_number):

    import subprocess

    subprocess.run(
        [
            "git",
            "config",
            "user.name",
            "calculator-agent"
        ],
        check=True
    )

    subprocess.run(
        [
            "git",
            "config",
            "user.email",
            "agent@github.local"
        ],
        check=True
    )

    subprocess.run(
        ["git", "add", "."],
        check=True
    )

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Agent implementation for issue #{issue_number}"
        ],
        check=True
    )

def push_branch(branch_name):

    result = subprocess.run(
        [
            "git",
            "push",
            "--set-upstream",
            "origin",
            branch_name
        ],
        capture_output=True,
        text=True
    )

    print("=== PUSH STDOUT ===")
    print(result.stdout)

    print("=== PUSH STDERR ===")
    print(result.stderr)

    result.check_returncode()

