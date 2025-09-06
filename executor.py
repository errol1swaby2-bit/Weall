# executor.py
import time
import json
import secrets
from collections import defaultdict
from typing import Optional

from wecoin import WeCoinLedger   # compiled Rust-backed module
import ipfshttpclient
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# Helper encryption utilities
def generate_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key

def encrypt_message(pub_key, message: str) -> bytes:
    return pub_key.encrypt(
        message.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                     algorithm=hashes.SHA256(), label=None)
    )

def decrypt_message(priv_key, ciphertext: bytes) -> str:
    return priv_key.decrypt(
        ciphertext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                     algorithm=hashes.SHA256(), label=None)
    ).decode()

class WeAllExecutor:
    def __init__(self, dsl_file: str, poh_requirements: Optional[dict] = None):
        self.dsl_file = dsl_file
        self.ledger = WeCoinLedger()
        self.current_epoch = 0
        self.epoch_duration = 24 * 3600
        self.last_epoch_time = 0.0

        # In-memory app state (indexes, pointers)
        self.state = {
            "users": {},
            "posts": {},
            "comments": {},
            "disputes": {},
            "treasury": defaultdict(float),
            "messages": defaultdict(list),
            "proposals": {},
            "nfts": {}
        }

        self.next_post_id = 1
        self.next_comment_id = 1
        self.next_dispute_id = 1
        self.next_proposal_id = 1

        self.poh_requirements = poh_requirements or {}

        try:
            self.ipfs = ipfshttpclient.connect()
        except Exception as e:
            print(f"[IPFS] connection failed: {e}")
            self.ipfs = None

    # Utilities
    def _upload_to_ipfs(self, content: str) -> str:
        if not self.ipfs:
            raise RuntimeError("IPFS client not available")
        return self.ipfs.add_str(content)

    def _check_poh(self, user_id, action):
        required = self.get_required_poh(action)
        actual = self.state["users"].get(user_id, {}).get("poh_level", 0)
        return actual >= required

    def get_required_poh(self, action):
        return self.poh_requirements.get(action, 0)

    # Users
    def register_user(self, user_id, poh_level=1):
        if user_id in self.state["users"]:
            return {"ok": False, "error": "user_already_exists"}
        priv, pub = generate_keypair()
        self.state["users"][user_id] = {
            "poh_level": poh_level,
            "private_key": priv,
            "public_key": pub,
            "reputation": 1
        }
        # create and enable in ledger
        self.ledger.create_account(user_id)
        self.ledger.set_eligible(user_id, True)
        # event
        self.ledger.add_event("user_register", json.dumps({
            "user": user_id, "poh_level": poh_level
        }))
        return {"ok": True}

    # Governance
    def propose(self, user_id, title, description, pallet_ref):
        if not self._check_poh(user_id, "propose"):
            return {"ok": False, "error": "insufficient_poh"}
        pid = self.next_proposal_id
        self.next_proposal_id += 1
        self.state["proposals"][pid] = {
            "title": title,
            "description": description,
            "pallet_ref": pallet_ref,
            "votes": {},
            "status": "open",
            "created_by": user_id,
            "created_at": int(time.time())
        }
        self.ledger.add_event("proposal", json.dumps({
            "proposal_id": pid, "user": user_id, "title": title, "pallet_ref": pallet_ref
        }))
        return {"ok": True, "proposal_id": pid}

    def vote(self, user_id, proposal_id, option):
        if not self._check_poh(user_id, "vote"):
            return {"ok": False, "error": "insufficient_poh"}
        if proposal_id not in self.state["proposals"]:
            return {"ok": False, "error": "proposal_not_found"}
        rep = self.state["users"][user_id].get("reputation", 1)
        weight = int(rep ** 0.5) or 1
        self.state["proposals"][proposal_id]["votes"][user_id] = {"option": option, "weight": weight}
        self.ledger.add_event("vote", json.dumps({
            "proposal_id": proposal_id, "user": user_id, "option": option, "weight": weight
        }))
        return {"ok": True}

    # Reputation
    def grant_reputation(self, user_id, amount):
        if user_id not in self.state["users"]:
            return {"ok": False, "error": "user_not_registered"}
        self.state["users"][user_id]["reputation"] += amount
        self.ledger.add_event("reputation", json.dumps({
            "user": user_id, "delta": amount, "new_score": self.state["users"][user_id]["reputation"]
        }))
        return {"ok": True}

    def slash_reputation(self, user_id, amount):
        if user_id not in self.state["users"]:
            return {"ok": False, "error": "user_not_registered"}
        self.state["users"][user_id]["reputation"] = max(0, self.state["users"][user_id]["reputation"] - amount)
        self.ledger.add_event("reputation", json.dumps({
            "user": user_id, "delta": -amount, "new_score": self.state["users"][user_id]["reputation"]
        }))
        return {"ok": True}

    # Posts & Comments
    def create_post(self, user_id, content, tags=None, reward_amount=10):
        if not self._check_poh(user_id, "post"):
            return {"ok": False, "error": "insufficient_poh"}
        try:
            ipfs_hash = self._upload_to_ipfs(content)
        except Exception as e:
            return {"ok": False, "error": f"IPFS upload failed: {e}"}
        post_id = self.next_post_id
        self.next_post_id += 1
        self.state["posts"][post_id] = {
            "user": user_id,
            "content_hash": ipfs_hash,
            "tags": tags or [],
            "comments": [],
            "created_at": int(time.time())
        }
        # mint reward via ledger (note: deposit returns bool for mint success)
        minted = self.ledger.deposit(user_id, int(reward_amount))
        if not minted:
            # if mint failed due to cap, still add to pool but no coin reward
            self.ledger.add_event("reward_failed", json.dumps({
                "type": "post", "user": user_id, "post_id": post_id, "reason": "supply_cap"
            }))
        else:
            self.ledger.add_event("reward", json.dumps({"type": "post", "user": user_id, "amount": reward_amount}))
        # add to pool
        try:
            self.ledger.add_to_pool("creators", user_id)
        except Exception:
            pass
        # emit event
        self.ledger.add_event("post", json.dumps({
            "user": user_id, "post_id": post_id, "ipfs_hash": ipfs_hash, "tags": tags or []
        }))
        return {"ok": True, "post_id": post_id, "ipfs_hash": ipfs_hash}

    def create_comment(self, user_id, post_id, content, tags=None, reward_amount=5):
        if not self._check_poh(user_id, "comment"):
            return {"ok": False, "error": "insufficient_poh"}
        if post_id not in self.state["posts"]:
            return {"ok": False, "error": "post_not_found"}
        try:
            ipfs_hash = self._upload_to_ipfs(content)
        except Exception as e:
            return {"ok": False, "error": f"IPFS upload failed: {e}"}
        cid = self.next_comment_id
        self.next_comment_id += 1
        self.state["comments"][cid] = {
            "user": user_id,
            "content_hash": ipfs_hash,
            "tags": tags or [],
            "post_id": post_id,
            "created_at": int(time.time())
        }
        self.state["posts"][post_id]["comments"].append(cid)
        minted = self.ledger.deposit(user_id, int(reward_amount))
        if not minted:
            self.ledger.add_event("reward_failed", json.dumps({
                "type": "comment", "user": user_id, "comment_id": cid, "reason": "supply_cap"
            }))
        else:
            self.ledger.add_event("reward", json.dumps({"type": "comment", "user": user_id, "amount": reward_amount}))
        try:
            self.ledger.add_to_pool("creators", user_id)
        except Exception:
            pass
        self.ledger.add_event("comment", json.dumps({
            "user": user_id, "comment_id": cid, "post_id": post_id, "ipfs_hash": ipfs_hash, "tags": tags or []
        }))
        return {"ok": True, "comment_id": cid, "ipfs_hash": ipfs_hash}

    # Disputes / Jurors
    def create_dispute(self, reporter_id, target_post_id, description, reward_amount=15):
        if not self._check_poh(reporter_id, "dispute"):
            return {"ok": False, "error": "insufficient_poh"}
        if target_post_id not in self.state["posts"]:
            return {"ok": False, "error": "post_not_found"}
        try:
            ipfs_hash = self._upload_to_ipfs(description)
        except Exception as e:
            return {"ok": False, "error": f"IPFS upload failed: {e}"}
        dispute_id = self.next_dispute_id
        self.next_dispute_id += 1
        self.state["disputes"][dispute_id] = {
            "reporter": reporter_id,
            "target_post": target_post_id,
            "description_hash": ipfs_hash,
            "status": "open",
            "jurors": [],
            "votes": {},
            "created_at": int(time.time())
        }
        minted = self.ledger.deposit(reporter_id, int(reward_amount))
        if not minted:
            self.ledger.add_event("reward_failed", json.dumps({
                "type": "dispute_bounty", "user": reporter_id, "dispute_id": dispute_id, "reason": "supply_cap"
            }))
        else:
            self.ledger.add_event("reward", json.dumps({"type": "dispute_bounty", "user": reporter_id, "amount": reward_amount}))
        self.ledger.add_event("dispute_create", json.dumps({
            "dispute_id": dispute_id, "reporter": reporter_id, "target_post": target_post_id
        }))
        return {"ok": True, "dispute_id": dispute_id, "ipfs_hash": ipfs_hash}

    def assign_jurors(self, dispute_id, num_jurors=3):
        dispute = self.state["disputes"].get(dispute_id)
        if not dispute:
            return {"ok": False, "error": "dispute_not_found"}
        try:
            candidates = self.ledger.list_pool_members("jurors")
        except Exception as e:
            return {"ok": False, "error": f"ledger_error: {e}"}
        if not candidates:
            return {"ok": False, "error": "no_jurors"}
        chosen = secrets.SystemRandom().sample(candidates, min(num_jurors, len(candidates)))
        dispute["jurors"] = chosen
        self.ledger.add_event("jurors_assigned", json.dumps({
            "dispute_id": dispute_id, "jurors": chosen
        }))
        return {"ok": True, "jurors": chosen}

    def juror_vote(self, dispute_id, juror_id, decision):
        dispute = self.state["disputes"].get(dispute_id)
        if not dispute:
            return {"ok": False, "error": "dispute_not_found"}
        if juror_id not in dispute["jurors"]:
            return {"ok": False, "error": "not_a_juror"}
        dispute["votes"][juror_id] = decision
        self.ledger.add_event("juror_vote", json.dumps({
            "dispute_id": dispute_id, "juror": juror_id, "decision": decision
        }))
        return {"ok": True}

    def resolve_dispute(self, dispute_id):
        dispute = self.state["disputes"].get(dispute_id)
        if not dispute:
            return {"ok": False, "error": "dispute_not_found"}
        votes = list(dispute["votes"].values())
        if not votes:
            return {"ok": False, "error": "no_votes"}
        outcome = max(set(votes), key=votes.count)
        dispute["status"] = "resolved"
        self.ledger.add_event("dispute_resolution", json.dumps({
            "dispute_id": dispute_id, "outcome": outcome, "jurors": dispute["jurors"], "votes": dispute["votes"]
        }))
        # Optionally apply reputation changes / slashes
        return {"ok": True, "outcome": outcome}

    # NFTs
    def mint_nft(self, account, nft_id, metadata):
        if account not in self.state["users"]:
            return {"ok": False, "error": "user_not_registered"}
        try:
            ipfs_hash = self._upload_to_ipfs(metadata)
        except Exception as e:
            return {"ok": False, "error": f"IPFS upload failed: {e}"}
        minted = self.ledger.deposit(account, 20)
        if not minted:
            return {"ok": False, "error": "mint_failed_supply_cap"}
        self.state["nfts"][nft_id] = {"owner": account, "metadata_hash": ipfs_hash, "minted_at": int(time.time())}
        self.ledger.add_event("nft_minted", json.dumps({
            "nft_id": nft_id, "owner": account, "metadata_hash": ipfs_hash
        }))
        return {"ok": True, "nft_id": nft_id, "ipfs_hash": ipfs_hash}

    # Treasury
    def allocate(self, pool, amount):
        if self.state["treasury"][pool] >= amount:
            self.state["treasury"][pool] -= amount
            # deposit pool funds to ledger account named pool
            self.ledger.deposit(pool, int(amount))
            self.ledger.add_event("treasury_allocate", json.dumps({"pool": pool, "amount": amount}))
            return {"ok": True}
        return {"ok": False, "error": "insufficient_treasury"}

    def reclaim(self, pool, amount):
        self.state["treasury"][pool] += amount
        self.ledger.add_event("treasury_reclaim", json.dumps({"pool": pool, "amount": amount}))
        return {"ok": True}

    # Epochs
    def advance_epoch(self, force=False):
        now = time.time()
        if not force and now - self.last_epoch_time < self.epoch_duration:
            return {"ok": False, "error": "epoch_not_elapsed"}
        self.current_epoch += 1
        self.last_epoch_time = now
        # set ledger epoch
        self.ledger.set_epoch(self.current_epoch)
        winners = self.ledger.distribute_epoch_rewards(self.current_epoch)
        # rebuild pools in ledger based on PoH
        for uid, user in self.state["users"].items():
            try:
                self.ledger.add_to_pool("creators", uid)
            except Exception:
                pass
            if user["poh_level"] >= self.get_required_poh("juror"):
                try:
                    self.ledger.add_to_pool("jurors", uid)
                except Exception:
                    pass
            if user["poh_level"] >= self.get_required_poh("operator"):
                try:
                    self.ledger.add_to_pool("operators", uid)
                except Exception:
                    pass
        # event
        self.ledger.add_event("epoch_advance", json.dumps({"epoch": self.current_epoch, "winners": winners}))
        return {"ok": True, "epoch": self.current_epoch, "winners": winners}

    # Messages
    def send_message(self, from_user, to_user, message_text):
        if from_user not in self.state["users"] or to_user not in self.state["users"]:
            return {"ok": False, "error": "user_not_registered"}
        pub = self.state["users"][to_user]["public_key"]
        encrypted = encrypt_message(pub, message_text)
        self.state["messages"][to_user].append({
            "from": from_user,
            "encrypted": encrypted,
            "timestamp": int(time.time())
        })
        self.ledger.add_event("message_sent", json.dumps({"from": from_user, "to": to_user}))
        return {"ok": True}

    def read_messages(self, user_id):
        if user_id not in self.state["users"]:
            return {"ok": False, "error": "user_not_registered"}
        priv = self.state["users"][user_id]["private_key"]
        msgs = []
        for m in self.state["messages"][user_id]:
            try:
                text = decrypt_message(priv, m["encrypted"])
            except Exception:
                text = "[decryption_failed]"
            msgs.append({"from": m["from"], "text": text, "timestamp": m["timestamp"]})
        return msgs

    # Events helper
    def list_events(self, count: Optional[int] = None):
        try:
            s = self.ledger.list_events(count)
            return json.loads(s)
        except Exception as e:
            return {"ok": False, "error": str(e)}
