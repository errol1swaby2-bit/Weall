WeAll

WeAll is a decentralized social coordination protocol powered by PoH (Proof of Humanity).
Users can register, propose, vote, post, comment, and interact with a shared governance system.


---

Getting Started

Clone the repository and install dependencies

git clone https://github.com/errol1swaby2-bit/Weall.git
cd WeAll
pip install -r Requirements.txt

> Note: If you want to run tests, also install pytest:



pip install pytest


---

Run the Interactive CLI

The CLI is built into weall_runtime.py:

python weall_runtime.py

You’ll see a prompt:

Command (register/propose/vote/deposit/post/comment/show_post/show_posts/.../exit):

Type exit to quit.


---

Commands Overview

User & Identity Management

register – Register a new user with a Proof-of-Humanity (PoH) level.

deposit – Allocate funds to a treasury pool, increasing your stake for governance.


Proposal & Voting

propose – Submit a new proposal for community consideration.

vote – Cast a vote on an active proposal.

create_dispute – Initiate a dispute over a post, comment, or proposal outcome.

juror_vote – Cast a vote as a selected juror on a dispute.


Content Management

post – Create a new post.

comment – Add a comment to a post.

edit_post / delete_post – Modify or remove your post.

edit_comment / delete_comment – Modify or remove your comment.

show_post / show_posts – Display one or multiple posts.

list_user_posts / list_tag_posts – Filter posts by user or tag.


Dispute & Moderation

show_dispute / show_disputes – View the details of one or all active disputes.

report_post / report_comment – Flag a post or comment for review.


System & Diagnostics

show – Print the full internal state of the system, including users, proposals, treasury, and disputes.

---

Tests (Optional)

If you have tests in tests/, run:

pytest -q

This ensures your executor correctly loads and processes DSL files.


---

DSL File

The CLI automatically loads:

weall_dsl_v0.5.yaml

You can add additional DSLs in a new folder examples/ if desired.


---

Requirements

Your Requirements.txt should include:

pyyaml>=6.0
pytest>=7.0
packaging>=23.0
click>=8.0

Only pyyaml is strictly required to run the executor.

Others are optional but recommended for testing and CLI enhancements.
