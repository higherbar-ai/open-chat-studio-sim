#  Copyright (c) 2024 Dimagi, Inc.
#
#  BSD 3-Clause License: see LICENSE for details.

"""Open Chat Studio support functions for data generation and simulation."""

from ocs_api import OCSAPIClient
import logging
from athina.datasets import Dataset
from athina.keys import AthinaApiKey


class OCSBotToBotSimulator:
    """A class to simulate bot-to-bot conversations using the Open Chat Studio API."""

    def __init__(self, ocs_api_client: OCSAPIClient, exp_id: str, user_exp_id: str, part_id: str):
        """
        Initialize for bot-to-bot simulation.

        Args:
            ocs_api_client (OCSAPIClient): The OCS API client to use.
            exp_id (str): The ID of the AI assistant experiment.
            user_exp_id (str): The ID of the user simulator experiment.
            part_id (str): The ID of the participant to use.
        """

        # remember details for future calls
        self.ocs_api_client = ocs_api_client
        self.experiment_id = exp_id
        self.user_experiment_id = user_exp_id
        self.participant_id = part_id

    def exec_simulations(self, simulations: list[str, str], continue_on_error: bool = True,
                         max_exchanges: int = 20) -> list[dict]:
        """
        Execute a list of simulations.

        Args:
            simulations (list[str, str]): A list of simulations to run, each a tuple of (ID, context).
            continue_on_error (bool): Whether to continue to the next simulation if an error occurs. Default is True.
            max_exchanges (int): The maximum number of exchanges per simulation. Default is 20.

        Returns:
            list[dict]: List of dictionaries, each with the following keys: "simulation_id", "user_session_id",
            "experiment_session_id", "context", "messages".
        """

        results = []
        for simulation_id, simulation_context in simulations:
            # initialize for new simulation
            messages = []
            user_session_id = ""
            experiment_session_id = ""

            try:
                # create a new session for the user simulator experiment
                api_response = self.ocs_api_client.create_experiment_session(self.user_experiment_id,
                                                                             self.participant_id)
                user_session_id = api_response["id"]

                # send the context message as the first user message, use response as the first message to experiment
                api_response = self.ocs_api_client.send_new_api_message(self.user_experiment_id, simulation_context,
                                                                        user_session_id)
                user_message = api_response["response"]

                # create a new session for the experiment
                api_response = self.ocs_api_client.create_experiment_session(self.experiment_id, self.participant_id)
                experiment_session_id = api_response["id"]

                # loop while user_message is not "END"
                while user_message.strip().upper() != "END" and len(messages) < max_exchanges:
                    # send simulated user message to the experiment
                    api_response = self.ocs_api_client.send_new_api_message(self.experiment_id, user_message,
                                                                            experiment_session_id)
                    ai_message = api_response["response"]

                    # keep track of our exchanges
                    messages.append([user_message, ai_message])

                    # send AI response back to the user simulator
                    api_response = self.ocs_api_client.send_new_api_message(self.user_experiment_id,
                                                                            ai_message, user_session_id)
                    user_message = api_response["response"]
            except Exception as e:
                if continue_on_error:
                    # log the error and continue to the next simulation
                    logging.error(f"Continuing following simulation error: {str(e)}")
                    messages.append([f"ERROR: {str(e)}", "N/A"])
                else:
                    # re-raise the exception
                    raise

            # add to results
            results.append({
                "simulation_id": simulation_id,
                "user_session_id": user_session_id,
                "experiment_session_id": experiment_session_id,
                "context": simulation_context,
                "messages": messages
            })

        return results


def athina_create_dataset(athina_api_key: str, dataset_name: str, dataset_description: str,
                          dataset_rows: list[dict]) -> Dataset:
    """
    Create a new dataset in Athina.

    Args:
        athina_api_key (str): The Athina API key to use.
        dataset_name (str): The name of the dataset.
        dataset_description (str): The description of the dataset.
        dataset_rows (list[dict]): The data rows to include in the dataset.

    Returns:
        Dataset: The newly-created dataset.
    """

    AthinaApiKey.set_key(athina_api_key)
    return Dataset.create(name=dataset_name, description=dataset_description, rows=dataset_rows)
