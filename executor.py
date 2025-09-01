# weall_executor_poh_enforced.py
import yaml
import math
from collections import defaultdict

class WeAllExecutor:
    def __init__(self, dsl_file):
        self.dsl_file = dsl_file
        self.dsl = None
        self.state = {
            "users": {},        # user_id -> {"poh_level": int, "reputation": float}
            "proposals": {},    # proposal_id -> {"title": str, "description": str, "votes": {}, "status": str}
            "treasury": defaultdict(float),  # pool_name -> balance
            "posts": {},        # post_id -> {"user": str, "content_hash": str, "tags": list, "comments": list}
        }
        self.next_proposal_id = 1

    # --- DSL Loading ---
    def load_dsl(self):
        with open(self.dsl_file, "r") as f:
            self.dsl = yaml.safe_load(f)
        print(f"Loaded DSL: {self.dsl['Protocol']['Name']} v{self.dsl['Protocol']['Version']}")

    # --- User Management ---
    def register_user(self, user_id, poh_level=1):
        if user_id in self.state["users"]:
            print(f"User {user_id} already registered.")
            return
        self.state["users"][user_id] = {"poh_level": poh_level, "reputation": 1.0}
        print(f"Registered user {user_id} with PoH level {poh_level}.")

    # --- PoH Enforcement ---
    def check_poh_level(self, user_id, required_level):
        if user_id not in self.state["users"]:
            print(f"User {user_id} not registered.")
            return False
        user_level = self.state["users"][user_id]["poh_level"]
        if user_level < required_level:
            print(f"Action requires PoH level {required_level}. User {user_id} has level {user_level}.")
            return False
        return True

    # --- Governance ---
    def propose(self, user, title, description, pallet_reference, required_poh=1):
        if not self.check_poh_level(user, required_poh):
            return
        pid = self.next_proposal_id
        self.state["proposals"][pid] = {
            "title": title,
            "description": description,
            "pallet_reference": pallet_reference,
            "votes": {},
            "status": "open"
        }
        self.next_proposal_id += 1
        print(f"User {user} submitted proposal {pid}: {title}")
        return pid

    def vote(self, user, proposal_id, option, required_poh=1, quorum_ratio=0.6):
        if not self.check_poh_level(user, required_poh):
            return
        if proposal_id not in self.state["proposals"]:
            print(f"Proposal {proposal_id} does not exist.")
            return
        proposal = self.state["proposals"][proposal_id]
        if proposal["status"] != "open":
            print(f"Proposal {proposal_id} is already closed.")
            return

        # Record vote
        proposal["votes"][user] = {
            "option": option,
            "weight": 1.0  # or based on reputation
        }
        print(f"User {user} voted '{option}' on proposal {proposal_id} with weight 1.0")

        # Check quorum and auto-tally
        total_users = len(self.state["users"])
        quorum = math.ceil(total_users * quorum_ratio)
        if len(proposal["votes"]) >= quorum:
            print(f"Quorum reached ({len(proposal['votes'])}/{total_users}), auto-tallying proposal {proposal_id}...")
            self.tally_votes(proposal_id)

    def tally_votes(self, proposal_id):
        if proposal_id not in self.state["proposals"]:
            print(f"Proposal {proposal_id} not found.")
            return
        proposal = self.state["proposals"][proposal_id]
        votes = proposal["votes"]
        if not votes:
            print(f"No votes to tally for proposal {proposal_id}.")
            return

        # Tally by weight
        results = defaultdict(float)
        for v in votes.values():
            results[v["option"]] += v["weight"]

        proposal["status"] = "closed"
        print(f"Tally for proposal {proposal_id}: {dict(results)}")
        return dict(results)

    # --- Treasury ---
    def allocate_funds(self, pool_name, amount):
        self.state["treasury"][pool_name] += amount
        print(f"Allocated {amount} to treasury pool '{pool_name}'. New balance: {self.state['treasury'][pool_name]}")

    # --- Content / Messaging ---
    def create_post(self, user_id, content_hash, tags):
        post_id = len(self.state["posts"]) + 1
        self.state["posts"][post_id] = {"user": user_id, "content_hash": content_hash, "tags": tags, "comments": []}
        print(f"User {user_id} created post {post_id} with tags {tags}")
        return post_id

    def comment(self, user_id, post_id, comment_hash, tags=None):
        if post_id not in self.state["posts"]:
            print(f"Post {post_id} not found.")
            return
        comment_data = {"user": user_id, "hash": comment_hash}
        if tags:
            comment_data["tags"] = tags
        self.state["posts"][post_id]["comments"].append(comment_data)
        print(f"User {user_id} commented on post {post_id} with tags {tags if tags else 'none'}")

    # --- Post Management ---
    def edit_post(self, post_id, new_content=None, new_tags=None):
        if post_id not in self.state["posts"]:
            print(f"Post {post_id} not found.")
            return
        post = self.state["posts"][post_id]
        if new_content:
            post["content_hash"] = new_content
        if new_tags:
            post["tags"] = new_tags
        print(f"Post {post_id} updated.")

    def delete_post(self, post_id):
        if post_id in self.state["posts"]:
            del self.state["posts"][post_id]
            print(f"Post {post_id} deleted.")
        else:
            print(f"Post {post_id} not found.")
