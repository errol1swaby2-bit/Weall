# weall_runtime.py
from executor import WeAllExecutor  # Use the updated executor

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
    "list_tag_posts": 1
}

def run_cli():
    executor = WeAllExecutor(dsl_file="weall_dsl_v0.5.yaml")
    executor.load_dsl()

    while True:
        cmd = input(
            "\nCommand (register/propose/vote/deposit/post/comment/show_post/show_posts/edit_post/delete_post/edit_comment/delete_comment/list_user_posts/list_tag_posts/show/exit): "
        ).strip().lower()

        if cmd == "exit":
            break

        elif cmd == "register":
            user = input("User ID: ")
            poh = int(input("PoH Level: "))
            executor.register_user(user, poh)

        elif cmd == "propose":
            user = input("User ID: ")
            if not executor.check_poh_level(user, POH_REQUIREMENTS["propose"]):
                continue
            title = input("Proposal Title: ")
            description = input("Description: ")
            pallet = input("Pallet Reference: ")
            executor.propose(user, title, description, pallet)

        elif cmd == "vote":
            user = input("User ID: ")
            if not executor.check_poh_level(user, POH_REQUIREMENTS["vote"]):
                continue
            pid = int(input("Proposal ID: "))
            option = input("Vote Option: ")
            executor.vote(user, pid, option)
            # Auto-tally results are printed by executor.vote if quorum is reached

        elif cmd == "deposit":
            user = input("User ID: ")
            if not executor.check_poh_level(user, POH_REQUIREMENTS["deposit"]):
                continue
            pool = input("Pool name: ")
            amt = float(input("Amount: "))
            executor.allocate_funds(pool, amt)

        elif cmd == "post":
            user = input("User ID: ")
            if not executor.check_poh_level(user, POH_REQUIREMENTS["post"]):
                continue
            content = input("Post content (text or content hash): ")
            tags = input("Tags (comma separated): ").split(",")
            executor.create_post(user, content, tags)

        elif cmd == "comment":
            user = input("User ID: ")
            if not executor.check_poh_level(user, POH_REQUIREMENTS["comment"]):
                continue
            pid = int(input("Post ID: "))
            content = input("Comment content (text or content hash): ")
            tags = input("Tags for comment (comma separated, optional): ").split(",")
            executor.comment(user, pid, content, tags if tags != [""] else None)

        elif cmd == "show_post":
            pid = int(input("Post ID: "))
            post = executor.state["posts"].get(pid)
            if not post:
                print(f"Post {pid} not found.")
                continue
            print(f"\nPost ID: {pid}")
            print(f"User: {post['user']}")
            print(f"Content: {post['content_hash']}")
            print(f"Tags: {post['tags']}")
            comments = post.get("comments", [])
            if comments:
                print("Comments:")
                for c in comments:
                    tag_str = f" [tags: {c['tags']}]" if "tags" in c else ""
                    print(f" - {c['user']}: {c['hash']}{tag_str}")
            else:
                print("No comments.")

        elif cmd == "show_posts":
            print("\n=== Posts ===")
            for pid, post in executor.state["posts"].items():
                print(f"\nPost ID: {pid}")
                print(f"User: {post['user']}")
                print(f"Content: {post['content_hash']}")
                print(f"Tags: {post['tags']}")
                comments = post.get("comments", [])
                if comments:
                    print("Comments:")
                    for c in comments:
                        tag_str = f" [tags: {c['tags']}]" if "tags" in c else ""
                        print(f" - {c['user']}: {c['hash']}{tag_str}")
                else:
                    print("No comments.")

        elif cmd == "show":
            print("\n=== Current State ===")
            print("Users:", executor.state["users"])
            print("Proposals:", executor.state["proposals"])
            print("Treasury:", executor.state["treasury"])
            print("Posts:", executor.state["posts"])

        elif cmd in ["edit_post", "delete_post", "edit_comment", "delete_comment",
                     "list_user_posts", "list_tag_posts"]:
            user = input("User ID: ")
            if not executor.check_poh_level(user, POH_REQUIREMENTS[cmd]):
                continue

            if cmd == "edit_post":
                pid = int(input("Post ID: "))
                content = input("New content (leave blank to keep current): ").strip()
                tags = input("New tags (comma separated, leave blank to keep current): ").strip()
                executor.edit_post(pid, new_content=content or None,
                                   new_tags=tags.split(",") if tags else None)

            elif cmd == "delete_post":
                pid = int(input("Post ID: "))
                executor.delete_post(pid)

            elif cmd == "edit_comment":
                pid = int(input("Post ID: "))
                idx = int(input("Comment index (starting at 0): "))
                content = input("New content (leave blank to keep current): ").strip()
                tags = input("New tags (comma separated, leave blank to keep current): ").strip()
                executor.edit_comment(pid, idx, new_content=content or None,
                                      new_tags=tags.split(",") if tags else None)

            elif cmd == "delete_comment":
                pid = int(input("Post ID: "))
                idx = int(input("Comment index (starting at 0): "))
                executor.delete_comment(pid, idx)

            elif cmd == "list_user_posts":
                executor.list_posts_by_user(user)

            elif cmd == "list_tag_posts":
                tag = input("Tag: ")
                executor.list_posts_by_tag(tag)

        else:
            print("Unknown command.")

if __name__ == "__main__":
    run_cli()
