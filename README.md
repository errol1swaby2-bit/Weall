WeAll Protocol

Version: 0.5
Copyright (c) 2025 Errol Jacob Jones Swaby

WeAll is a decentralized social coordination protocol enabling democratic governance, community-driven funding, and modular extensibility. It is designed to empower communities while keeping the software and protocol fully open and free.


---

Table of Contents

1. Overview


2. Features


3. Architecture


4. Getting Started


5. Licenses


6. Contributing


7. Contact




---

Overview

WeAll allows communities to:

Create proposals and vote using a proof-of-humanity and reputation-based system.

Manage shared resources and funding in a transparent treasury.

Extend the protocol through modular DSL files and plugins.


The protocol emphasizes democratic participation, community ownership, and copyleft principles to ensure continued freedom and openness.


---

Features

Quadratic Voting: Voting power scales with the square root of reputation.

Proof-of-Humanity Enforcement: One identity = one reputation score.

Modular DSL System: Easily extend governance rules, treasury logic, and plugin behavior.

Automated Proposal Execution: Actions trigger automatically when quorum and conditions are met.

Open Participation: Anyone can join, propose, and vote.



---

Architecture

1. Core Modules:

Governance: Proposals, voting, reputation.

Treasury: Community funds management.

Posts: Decentralized content storage and interaction.



2. DSL Layer:

Defines rules, actions, and plugins.

Written in YAML, easily readable and extendable.



3. Executor:

Python runtime that interprets the DSL.

Ensures protocol rules are enforced programmatically.





---

Getting Started

1. Clone the repository:



git clone https://github.com/yourusername/weall.git
cd weall

2. Install dependencies (Python 3.10+ recommended):



pip install -r requirements.txt

3. Run the executor:



python weall_executor.py

4. Modify or create DSL files in dsl/ to test governance, proposals, and modules.




---

Licenses

Code: GNU Affero General Public License v3.0 (LICENSE-AGPL.txt)

Protocol / DSL / Documentation: Creative Commons Attribution-ShareAlike 4.0 (LICENSE-CC-BY-SA.txt)


This ensures that all modifications remain open, and anyone running WeAll or derivative works on a network must share their changes.


---

Contributing

We welcome contributions! By contributing, you agree to:

1. Submit code and documentation under the same licenses.


2. Acknowledge that contributions are initially under Errol Jacob Jones Swaby’s copyright until A.R.S. is established.


3. Respect community governance rules and open-source principles.



Please see CONTRIBUTING.md for full guidelines.


---

Contact

Author: Errol Jacob Jones Swaby

Project: WeAll – Architects of Regenerative Sovereignty

Email: errol1swaby2@gmail.com
