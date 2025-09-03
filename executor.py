import yaml
import math
import time
import secrets
from collections import defaultdict


class WeAllExecutor:
    """
    Lightweight in-memory executor for the WeAll protocol MVP.
    Provides governance, content, and dispute flows with PoH-gated actions.
    """

    def __init__(self, dsl_file, poh_requirements=None):
        self.dsl_file = dsl_file
        self.dsl = None

        # Core state
        self.state = {
            "users": {},         # user_id -> {poh_level, reputation, balance}
            "proposals": {},     # proposal_id -> {...}
            "treasury": defaultdict(float),
            "posts": {},         # post_id -> {user, content_hash, tags, comments: [comment_ids]}
            "comments": {},      # comment_id -> {user, content, tags, post_id}
            "disputes": {},      # dispute_id -> {...}
        }

        # ID counters
        self.next_proposal_id = 1
        self.next_dispute_id = 1
        self.next_post_id = 1
        self.next_comment_id = 1

        # Defaults
        self.default_jury_size = 7
        self.appeal_multiplier = 2
        self.dispute_stake_amount = 0.01
        self.juror_quorum_ratio = 0.5  # fraction of jurors required to resolve

        # Centralized PoH requirements (can be overridden by caller or DSL)
        # Keys should match action names used throughout the executor/CLI.
        self.poh_requirements = poh_requirements or {
            "propose": 1,
            "vote": 1,
            "post": 1,
            "comment": 1,
            "edit_post": 1,
            "delete_post": 1,
            "edit_comment": 1,
            "delete_comment": 1,
            "report": 2,
            "dispute": 2,
            "juror": 3,
        }

    # ------------------------
    # Internal helpers
    # ------------------------
    def _next_proposal_id(self):
        pid = self.next_proposal_id
        self.next_proposal_id += 1
        return pid

    def _next_dispute_id(self):
        did = self.next_dispute_id
        self.next_dispute_id += 1
        return did

    def _next_post_id(self):
        pid = self.next_post_id
        self.next_post_id += 1
        return pid

    def _next_comment_id(self):
        cid = self.next_comment_id
        self.next_comment_id += 1
        return cid

    def get_required_poh(self, action, fallback=1):
        """
        Resolve PoH requirement for an action from:
        1) self.poh_requirements (explicit override), else
        2) DSL (future extension), else
        3) fallback.
        """
        return self.poh_requirements.get(action, fallback)

    # ------------------------
    # DSL Loading
    # ------------------------
    def load_dsl(self):
        with open(self.dsl_file, "r") as f:
            self.dsl = yaml.safe_load(f)
        print(f"Loaded DSL: {self.dsl['Protocol']['Name']} v{self.dsl['Protocol']['Version']}")

    # ------------------------
    # User Management
    # ------------------------
    def register_user(self, user_id, poh_level=1, balance=0.0):
        if user_id in self.state["users"]:
            msg = f"User {user_id} already registered."
            print(msg)
            return {"ok": False, "error": msg}
        self.state["users"][user_id] = {
            "poh_level": poh_level,
            "reputation": 1.0,
            "balance": balance,
        }
        msg = f"Registered user {user_id} with PoH level {poh_level} and balance {balance}."
        print(msg)
        return {"ok": True}

    def check_poh_level(self, user_id, required_level):
        if user_id not in self.state["users"]:
            print(f"User {user_id} not registered.")
            return False
        user_level = self.state["users"][user_id]["poh_level"]
        if user_level < required_level:
            print(f"Action requires PoH level {required_level}. User {user_id} has level {user_level}.")
            return False
        return True

    # ------------------------
    # Governance
    # ------------------------
    def propose(self, user, title, description, pallet_reference, required_poh=None):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("propose", 1)
        if not self.check_poh_level(user, required_poh):
            return {"ok": False, "error": "insufficient_poh"}
        pid = self._next_proposal_id()
        self.state["proposals"][pid] = {
            "title": title,
            "description": description,
            "pallet_reference": pallet_reference,
            "votes": {},           # user_id -> {option, weight}
            "status": "open",
            "finalized": False,    # prevents double tally
        }
        print(f"User {user} submitted proposal {pid}: {title}")
        return {"ok": True, "proposal_id": pid}

    def vote(self, user, proposal_id, option, required_poh=None, quorum_ratio=0.6):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("vote", 1)
        if not self.check_poh_level(user, required_poh):
            return {"ok": False, "error": "insufficient_poh"}
        if proposal_id not in self.state["proposals"]:
            msg = f"Proposal {proposal_id} does not exist."
            print(msg)
            return {"ok": False, "error": "not_found"}
        proposal = self.state["proposals"][proposal_id]
        if proposal["status"] != "open" or proposal.get("finalized"):
            msg = f"Proposal {proposal_id} is already closed."
            print(msg)
            return {"ok": False, "error": "closed"}

        reputation = self.state["users"][user]["reputation"]
        weight = math.sqrt(max(reputation, 0.0))
        proposal["votes"][user] = {"option": option, "weight": weight}
        print(f"User {user} voted '{option}' on proposal {proposal_id} with weight {weight:.2f}")

        total_eligible = len([u for u, meta in self.state["users"].items()
                              if meta["poh_level"] >= required_poh])
        quorum = math.ceil(total_eligible * quorum_ratio)
        if len(proposal["votes"]) >= quorum:
            print(f"Quorum reached ({len(proposal['votes'])}/{total_eligible}), auto-tallying proposal {proposal_id}...")
            return self.tally_votes(proposal_id)

        return {"ok": True}

    def tally_votes(self, proposal_id):
        proposal = self.state["proposals"].get(proposal_id)
        if not proposal:
            print(f"Proposal {proposal_id} not found.")
            return {"ok": False, "error": "not_found"}
        if proposal.get("finalized"):
            print(f"Proposal {proposal_id} already finalized.")
            return {"ok": False, "error": "finalized"}

        votes = proposal["votes"]
        if not votes:
            print(f"No votes to tally for proposal {proposal_id}.")
            return {"ok": False, "error": "no_votes"}
        results = defaultdict(float)
        for v in votes.values():
            results[v["option"]] += v["weight"]

        proposal["status"] = "closed"
        proposal["finalized"] = True
        print(f"Tally for proposal {proposal_id}: {dict(results)}")
        return {"ok": True, "results": dict(results)}

    # ------------------------
    # Treasury
    # ------------------------
    def allocate_funds(self, pool_name, amount):
        self.state["treasury"][pool_name] += float(amount)
        print(f"Allocated {amount} to treasury pool '{pool_name}'. New balance: {self.state['treasury'][pool_name]}")
        return {"ok": True, "balance": self.state["treasury"][pool_name]}

    # ------------------------
    # Content / Messaging
    # ------------------------
    def create_post(self, user_id, content, tags, required_poh=None):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("post", 1)
        if not self.check_poh_level(user_id, required_poh):
            return {"ok": False, "error": "insufficient_poh"}
        post_id = self._next_post_id()
        self.state["posts"][post_id] = {
            "user": user_id,
            "content_hash": content,
            "tags": tags or [],
            "comments": []
        }
        print(f"User {user_id} created post {post_id} with tags {tags}")
        return {"ok": True, "post_id": post_id}

    def edit_post(self, post_id, new_content=None, new_tags=None, user_id=None, required_poh=None):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("edit_post", 1)
        if user_id is not None and not self.check_poh_level(user_id, required_poh):
            return {"ok": False, "error": "insufficient_poh"}
        post = self.state["posts"].get(post_id)
        if not post:
            msg = f"Post {post_id} not found."
            print(msg)
            return {"ok": False, "error": "not_found"}
        if new_content is not None and new_content != "":
            post["content_hash"] = new_content
        if new_tags is not None:
            post["tags"] = new_tags
        print(f"Post {post_id} updated.")
        return {"ok": True}

    def delete_post(self, post_id, user_id=None, required_poh=None):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("delete_post", 1)
        if user_id is not None and not self.check_poh_level(user_id, required_poh):
            return {"ok": False, "error": "insufficient_poh"}
        post = self.state["posts"].get(post_id)
        if not post:
            msg = f"Post {post_id} not found."
            print(msg)
            return {"ok": False, "error": "not_found"}

        # Remove linked comments
        for cid in list(post["comments"]):
            if cid in self.state["comments"]:
                del self.state["comments"][cid]
        del self.state["posts"][post_id]
        print(f"Post {post_id} and its comments were deleted.")
        return {"ok": True}

    def create_comment(self, user_id, post_id, content, tags=None, comment_id=None, required_poh=None):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("comment", 1)
        if not self.check_poh_level(user_id, required_poh):
            return {"ok": False, "error": "insufficient_poh"}
        if post_id not in self.state["posts"]:
            msg = f"Post {post_id} not found."
            print(msg)
            return {"ok": False, "error": "not_found"}
        cid = comment_id or self._next_comment_id()
        self.state["comments"][cid] = {
            "user": user_id,
            "content": content,
            "tags": tags,
            "post_id": post_id
        }
        self.state["posts"][post_id]["comments"].append(cid)
        # keep counter monotonic if caller supplied a manual comment_id
        self.next_comment_id = max(self.next_comment_id, cid + 1)
        print(f"User {user_id} commented on post {post_id} with tags {tags if tags else 'none'} (comment ID {cid})")
        return {"ok": True, "comment_id": cid}

    def edit_comment(self, comment_id, new_content=None, new_tags=None, user_id=None, required_poh=None):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("edit_comment", 1)
        if user_id is not None and not self.check_poh_level(user_id, required_poh):
            return {"ok": False, "error": "insufficient_poh"}
        comment = self.state["comments"].get(comment_id)
        if not comment:
            msg = f"Comment {comment_id} not found."
            print(msg)
            return {"ok": False, "error": "not_found"}
        if new_content is not None and new_content != "":
            comment["content"] = new_content
        if new_tags is not None:
            comment["tags"] = new_tags
        print(f"Comment {comment_id} updated.")
        return {"ok": True}

    def delete_comment(self, comment_id, user_id=None, required_poh=None):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("delete_comment", 1)
        if user_id is not None and not self.check_poh_level(user_id, required_poh):
            return {"ok": False, "error": "insufficient_poh"}
        comment = self.state["comments"].get(comment_id)
        if not comment:
            msg = f"Comment {comment_id} not found."
            print(msg)
            return {"ok": False, "error": "not_found"}
        post_id = comment["post_id"]
        if post_id in self.state["posts"]:
            if comment_id in self.state["posts"][post_id]["comments"]:
                self.state["posts"][post_id]["comments"].remove(comment_id)
        del self.state["comments"][comment_id]
        print(f"Comment {comment_id} deleted.")
        return {"ok": True}

    # ------------------------
    # Dispute System
    # ------------------------
    def _level2_candidates(self):
        return [uid for uid, meta in self.state["users"].items() if meta.get("poh_level", 0) >= 2]

    def _level3_candidates(self):
        return [uid for uid, meta in self.state["users"].items() if meta.get("poh_level", 0) >= 3]

    def create_dispute(self, subject_type, subject_id, complainant, description, required_poh=None):
        required_poh = required_poh if required_poh is not None else self.get_required_poh("dispute", 2)
        if not self.check_poh_level(complainant, required_poh):
            print("Only sufficiently verified users may create disputes.")
            return {"ok": False, "error": "insufficient_poh"}

        did = self._next_dispute_id()
        dispute = {
            "dispute_id": did,
            "subject_type": subject_type,  # "post" | "comment"
            "subject_id": subject_id,
            "complainant": complainant,
            "description": description,
            "created_at": time.time(),
            "status": "open",
            "selected_jurors": [],
            "juror_votes": {},        # juror_id -> decision ("valid"/"invalid")
            "jury_size": self.default_jury_size,
            "appeal": None,
            "stake_pool": 0.0
        }
        self.state["disputes"][did] = dispute
        print(f"Dispute {did} created by {complainant} about {subject_type} {subject_id}.")
        self.select_jurors_for_dispute(did)
        return {"ok": True, "dispute_id": did}

    def select_jurors_for_dispute(self, dispute_id):
        dispute = self.state["disputes"].get(dispute_id)
        if not dispute:
            return {"ok": False, "error": "not_found"}
        candidates = self._level3_candidates()
        if len(candidates) < dispute["jury_size"]:
            print(f"Not enough level 3 users to serve as jurors. Only {len(candidates)} available.")
            dispute["selected_jurors"] = candidates
        else:
            dispute["selected_jurors"] = secrets.SystemRandom().sample(candidates, dispute["jury_size"])
        print(f"Selected jurors for dispute {dispute_id}: {dispute['selected_jurors']}")
        return {"ok": True, "jurors": list(dispute["selected_jurors"])}

    def juror_vote(self, juror_id, dispute_id, decision):
        dispute = self.state["disputes"].get(dispute_id)
        if not dispute:
            msg = f"Dispute {dispute_id} not found."
            print(msg)
            return {"ok": False, "error": "not_found"}
        if juror_id not in dispute["selected_jurors"]:
            msg = f"User {juror_id} is not a juror for dispute {dispute_id}."
            print(msg)
            return {"ok": False, "error": "not_juror"}
        dispute["juror_votes"][juror_id] = decision
        print(f"Juror {juror_id} voted '{decision}' on dispute {dispute_id}")
        self.check_dispute_resolution(dispute_id)
        return {"ok": True}

    def check_dispute_resolution(self, dispute_id):
        dispute = self.state["disputes"].get(dispute_id)
        if not dispute:
            return {"ok": False, "error": "not_found"}
        if dispute["status"] != "open":
            return {"ok": True, "status": dispute["status"]}

        votes = dispute["juror_votes"]
        if len(votes) < math.ceil(dispute["jury_size"] * self.juror_quorum_ratio):
            # Not enough jurors voted yet
            return {"ok": True, "status": "open"}

        # Tally votes
        results = defaultdict(int)
        for d in votes.values():
            results[d] += 1

        # Decide outcome
        max_votes = max(results.values())
        winners = [k for k, v in results.items() if v == max_votes]
        dispute["status"] = "closed"
        dispute["decision"] = winners[0] if len(winners) == 1 else "tie"
        print(f"Dispute {dispute_id} resolved. Decision: {dispute['decision']}")

        # Apply penalties/removals
        if dispute["decision"] == "valid":
            subject_type = dispute["subject_type"]
            subject_id = dispute["subject_id"]
            if subject_type == "post" and subject_id in self.state["posts"]:
                # remove comments too
                for cid in list(self.state["posts"][subject_id]["comments"]):
                    if cid in self.state["comments"]:
                        del self.state["comments"][cid]
                del self.state["posts"][subject_id]
                print(f"Post {subject_id} removed due to dispute resolution.")
            elif subject_type == "comment" and subject_id in self.state["comments"]:
                # unlink from its post
                p_id = self.state["comments"][subject_id]["post_id"]
                if p_id in self.state["posts"]:
                    if subject_id in self.state["posts"][p_id]["comments"]:
                        self.state["posts"][p_id]["comments"].remove(subject_id)
                del self.state["comments"][subject_id]
                print(f"Comment {subject_id} removed due to dispute resolution.")

        return {"ok": True, "status": "closed", "decision": dispute.get("decision")}

    # ------------------------
    # Reporting (creates disputes)
    # ------------------------
    def report_post(self, reporter, post_id, description):
        required_poh = self.get_required_poh("report", 2)
        if post_id not in self.state["posts"]:
            print(f"Post {post_id} not found.")
            return {"ok": False, "error": "not_found"}
        if not self.check_poh_level(reporter, required_poh):
            print("Reporter must have sufficient PoH level to report.")
            return {"ok": False, "error": "insufficient_poh"}
        return self.create_dispute("post", post_id, reporter, description)

    def report_comment(self, reporter, post_id, comment_id, description):
        required_poh = self.get_required_poh("report", 2)
        post = self.state["posts"].get(post_id)
        if not post:
            print(f"Post {post_id} not found.")
            return {"ok": False, "error": "not_found"}
        if comment_id not in self.state["comments"]:
            print(f"Comment {comment_id} not found.")
            return {"ok": False, "error": "not_found"}
        if not self.check_poh_level(reporter, required_poh):
            print("Reporter must have sufficient PoH level to report.")
            return {"ok": False, "error": "insufficient_poh"}
        return self.create_dispute("comment", comment_id, reporter, description)
