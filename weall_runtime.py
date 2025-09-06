# weall_runtime.py
from executor import WeAllExecutor
from collections import defaultdict

POH_REQUIREMENTS = {
    "propose": 3,
    "vote": 2,
    "post": 2,
    "comment": 2,
    "dispute": 3,
    "juror": 3,
    "operator": 3
}

def safe_int_input(prompt):
    try:
        return int(input(prompt))
    except Exception:
        print("Invalid input, expected a number.")
        return None

def run_cli():
    executor = WeAllExecutor(dsl_file="weall_dsl_v0.5.yaml", poh_requirements=POH_REQUIREMENTS)
    print("WeAll CLI started. Type 'exit' to quit.")

    while True:
        cmd = input("\nCommand (register/propose/vote/post/comment/show_post/show_posts/"
                    "create_dispute/assign_jurors/juror_vote/resolve_dispute/deposit/transfer/balance/"
                    "mint_nft/list_events/advance_epoch/exit): ").strip().lower()
        if cmd == "exit":
            break
        elif cmd == "register":
            user = input("User ID: ").strip()
            poh = safe_int_input("PoH Level: ")
            res = executor.register_user(user, poh_level=poh)
            print(res)
        elif cmd == "propose":
            user = input("User ID: ").strip()
            title = input("Title: ").strip()
            desc = input("Description: ").strip()
            pallet = input("Pallet ref: ").strip()
            print(executor.propose(user, title, desc, pallet))
        elif cmd == "vote":
            user = input("User ID: ").strip()
            pid = safe_int_input("Proposal ID: ")
            option = input("Option: ").strip()
            print(executor.vote(user, pid, option))
        elif cmd == "post":
            user = input("User ID: ").strip()
            content = input("Content: ").strip()
            tags = input("Tags (comma-separated, optional): ").strip()
            tags_list = [t.strip() for t in tags.split(",")] if tags else []
            print(executor.create_post(user, content, tags=tags_list))
        elif cmd == "comment":
            user = input("User ID: ").strip()
            pid = safe_int_input("Post ID: ")
            content = input("Comment: ").strip()
            tags = input("Tags (comma-separated, optional): ").strip()
            tags_list = [t.strip() for t in tags.split(",")] if tags else []
            print(executor.create_comment(user, pid, content, tags=tags_list))
        elif cmd == "create_dispute":
            user = input("Reporter ID: ").strip()
            pid = safe_int_input("Target post ID: ")
            desc = input("Description: ").strip()
            print(executor.create_dispute(user, pid, desc))
        elif cmd == "assign_jurors":
            did = safe_int_input("Dispute ID: ")
            num = safe_int_input("Number jurors: ") or 3
            print(executor.assign_jurors(did, num))
        elif cmd == "juror_vote":
            did = safe_int_input("Dispute ID: ")
            juror = input("Juror ID: ").strip()
            decision = input("Decision (guilty/innocent/other): ").strip()
            print(executor.juror_vote(did, juror, decision))
        elif cmd == "resolve_dispute":
            did = safe_int_input("Dispute ID: ")
            print(executor.resolve_dispute(did))
        elif cmd == "deposit":
            user = input("User ID: ").strip()
            amt = safe_int_input("Amount (integer): ")
            try:
                ok = executor.ledger.deposit(user, int(amt))
                print({"ok": ok})
            except Exception as e:
                print({"ok": False, "error": str(e)})
        elif cmd == "transfer":
            a = input("From: ").strip()
            b = input("To: ").strip()
            amt = safe_int_input("Amount: ")
            print(executor.ledger.transfer(a, b, int(amt)))
        elif cmd == "balance":
            user = input("User ID: ").strip()
            print(executor.ledger.balance(user))
        elif cmd == "mint_nft":
            user = input("User ID: ").strip()
            nft_id = input("NFT id: ").strip()
            metadata = input("Metadata (json text): ").strip()
            print(executor.mint_nft(user, nft_id, metadata))
        elif cmd == "list_events":
            c = safe_int_input("How many recent events (enter for all): ")
            c = c if c is not None else None
            print(executor.list_events(count=c))
        elif cmd == "advance_epoch":
            print(executor.advance_epoch(force=True))
        elif cmd == "show_post":
            pid = safe_int_input("Post ID: ")
            print(executor.state["posts"].get(pid, "not found"))
        elif cmd == "show_posts":
            for pid, post in executor.state["posts"].items():
                print(pid, post)
        else:
            print("Unknown command.")

if __name__ == "__main__":
    run_cli()
