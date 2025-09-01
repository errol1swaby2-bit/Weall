import yaml
from rich import print
from rich.table import Table

# --- Load DSL (multiple documents) ---
with open("weall_dsl.yaml") as f:
    docs = list(yaml.safe_load_all(f))

# Merge all YAML documents into a single dictionary
dsl = {}
for doc in docs:
    if doc is not None:
        dsl.update(doc)

# --- List top-level sections ---
print("[bold cyan]WeAll DSL loaded![/bold cyan]")
sections = list(dsl.keys())
table = Table(title="Top-Level Sections", show_lines=True)
table.add_column("Section", style="magenta")
for sec in sections:
    table.add_row(sec)
print(table)

# --- Index actions for quick lookup ---
actions = {a["name"]: a for a in dsl.get("actions", [])}

def execute_action(action_name, input_data=None):
    if action_name not in actions:
        return f"[red]Unknown action[/red]: {action_name}"
    action = actions[action_name]
    print(f"[green]Executing[/green]: {action['name']}")
    # Stub executor – here you’d wire to substrate pallet logic later
    return {"action": action_name, "input": input_data}

if __name__ == "__main__":
    print("[bold cyan]WeAll DSL Runner Ready[/bold cyan]")
    print("[yellow]Type 'quit' to exit[/yellow]\n")

    while True:
        cmd = input("Enter action (or 'quit'): ").strip()
        if cmd.lower() == "quit":
            print("[bold red]Exiting DSL runner[/bold red]")
            break
        result = execute_action(cmd)
        print(result)
