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

register – Register a user with a PoH level

propose – Submit a new proposal

vote – Vote on proposals

deposit – Allocate funds to a treasury pool

post – Create a post

comment – Add a comment to a post

show_post / show_posts – Display posts

edit_post / delete_post / edit_comment / delete_comment – Modify content

list_user_posts / list_tag_posts – Filter posts

show – Print full internal state



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
