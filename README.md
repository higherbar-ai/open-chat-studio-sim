# open-chat-studio-sim

This project includes a series of Jupyter notebooks and supporting Python modules for data generation and simulation 
with [Dimagi's Open Chat Studio](https://github.com/dimagi/open-chat-studio).

## Prerequisites

- Python 3.11
- pip

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/higherbar-ai/open-chat-studio-sim.git
    ```

2. Navigate to the project directory:

    ```bash
    cd open-chat-studio-sim
    ```

3. Create a virtual environment:

    ```bash
    python3 -m venv .venv
    ```

4. Activate the virtual environment:

    ```bash
    source .venv/bin/activate
    ```

5. Install the project dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

See the individual notebooks for usage instructions (and any further setup requirements):

* `simulate-queries.ipynb` - Executing single-prompt queries against a chatbot experiment 
* `replay-conversations.ipynb` - Replaying conversations with a chatbot experiment 
* `simulate-queries.ipynb` - Using one chatbot experiment to simulate users interacting with a second chatbot experiment 

## Credits

This toolkit was developed by [Higher Bar AI](https://higherbar.ai), a public benefit corporation, 
for and in collaboration with [Dimagi](https://dimagi.com). The project was generously funded by
the [Bill & Melinda Gates Foundation](https://www.gatesfoundation.org/).
