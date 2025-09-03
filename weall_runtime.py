from executor import WeAllExecutor

# Default required PoH levels per action
POH_REQUIREMENTS = {
    "propose": 3,
    "vote": 2,
    "post": 2,
    "comment": 2,
    "edit_post": 2,
    "delete_post": 2,
    "edit_comment": 2,
    "delete_comment": 2,
    "deposit": 2,
    "list_user_posts": 1,
    "list_tag_posts": 1,
    "report": 2,
    "dispute": 3
}

def safe_int_input(prompt):
    try:
        return int(input(prompt))
    except ValueError:
        print("Invalid input, expected a number.")
        return None

def run_cli():
    executor = WeAllExecutor(dsl_file="weall_dsl_v0.5.yaml")
    executor.load_dsl()

    while True:
        cmd = input(
            "\nCommand (register/propose/vote/post/comment/show_post/show_posts/edit_post/delete_post/"
            "edit_comment/delete_comment/list_user_posts/list_tag_posts/report_post/report_comment/"
            "create_dispute/juror_vote/show_disputes/show_dispute/exit): "
        ).strip().lower()

        if cmd == "exit":
            break

        elif cmd == "register":
            user = input("User ID: ")
            poh = safe_int_input("PoH Level: ")
            executor.register_user(user, poh_level=poh)

        elif cmd == "propose":
            user = input("User ID: ")
            title = input("Proposal title: ")
            desc = input("Proposal description: ")
            pallet = input("Pallet reference: ")
            executor.propose(user, title, desc, pallet, required_poh=POH_REQUIREMENTS["propose"])

        elif cmd == "vote":
            user = input("User ID: ")
            pid = safe_int_input("Proposal ID: ")
            option = input("Vote option: ")
            executor.vote(user, pid, option, required_poh=POH_REQUIREMENTS["vote"])

        elif cmd == "post":
            user = input("User ID: ")
            content = input("Post content hash: ")
            tags = input("Tags (comma-separated): ").split(",")
            executor.create_post(user, content, tags)

        elif cmd == "comment":
            user = input("User ID: ")
            pid = safe_int_input("Post ID: ")
            content = input("Comment content hash: ")
            tags = input("Tags (comma-separated, optional): ").split(",") if input("Add tags? (y/n): ").lower() == "y" else None
            executor.create_comment(user, pid, content, tags)

        elif cmd == "edit_post":
            pid = safe_int_input("Post ID to edit: ")
            content = input("New content (leave blank to keep): ")
            tags = input("New tags comma-separated (leave blank to keep): ").split(",") if input("Edit tags? (y/n): ").lower() == "y" else None
            executor.edit_post(pid, new_content=content or None, new_tags=tags)

        elif cmd == "delete_post":
            pid = safe_int_input("Post ID to delete: ")
            executor.delete_post(pid)

        elif cmd == "edit_comment":
            cid = safe_int_input("Comment ID to edit: ")
            content = input("New content (leave blank to keep): ")
            tags = input("New tags comma-separated (leave blank to keep): ").split(",") if input("Edit tags? (y/n): ").lower() == "y" else None
            executor.edit_comment(cid, new_content=content or None, new_tags=tags)

        elif cmd == "delete_comment":
            cid = safe_int_input("Comment ID to delete: ")
            executor.delete_comment(cid)

        elif cmd == "list_user_posts":
            user = input("User ID: ")
            posts = [pid for pid, p in executor.state["posts"].items() if p["user"] == user]
            print(f"Posts by {user}: {posts}")

        elif cmd == "list_tag_posts":
            tag = input("Tag to search: ")
            posts = [pid for pid, p in executor.state["posts"].items() if tag in p["tags"]]
            print(f"Posts with tag '{tag}': {posts}")

        elif cmd == "report_post":
            user = input("Reporter ID: ")
            pid = safe_int_input("Post ID to report: ")
            desc = input("Report description: ")
            executor.report_post(user, pid, desc)

        elif cmd == "report_comment":
            user = input("Reporter ID: ")
            pid = safe_int_input("Post ID of comment: ")
            cid = safe_int_input("Comment ID to report: ")
            desc = input("Report description: ")
            executor.report_comment(user, pid, cid, desc)

        elif cmd == "create_dispute":
            user = input("User ID: ")
            stype = input("Dispute subject type (post/comment): ")
            sid = safe_int_input("Subject ID: ")
            desc = input("Dispute description: ")
            executor.create_dispute(stype, sid, user, desc)

        elif cmd == "juror_vote":
            juror = input("Juror ID: ")
            did = safe_int_input("Dispute ID: ")
            decision = input("Decision (valid/invalid): ")
            executor.juror_vote(juror, did, decision)

        elif cmd == "show_disputes":
            for did, dispute in executor.state["disputes"].items():
                print(f"{did}: {dispute}")

        elif cmd == "show_dispute":
            did = safe_int_input("Dispute ID: ")
            dispute = executor.state["disputes"].get(did)
            if dispute:
                print(dispute)
            else:
                print(f"Dispute {did} not found.")

        elif cmd == "show_post":
            pid = safe_int_input("Post ID: ")
            post = executor.state["posts"].get(pid)
            print(post if post else f"Post {pid} not found.")

        elif cmd == "show_posts":
            for pid, post in executor.state["posts"].items():
                print(f"{pid}: {post}")

        else:
            print("Unknown command.")

if __name__ == "__main__":
    run_cli()
