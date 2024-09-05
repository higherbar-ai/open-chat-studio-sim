#  Copyright (c) 2024 Dimagi, Inc.
#
#  BSD 3-Clause License: see LICENSE for details.
#
#  September 4, 2024: generated based on schema at https://chatbots.dimagi.com/api/schema/ (schema snapshot saved to
#                     ocs-api-schema.yaml)

"""Open Chat Studio API wrapper with timeouts and tenacity retries."""

import requests
from tenacity import retry, stop_after_attempt, wait_fixed
import logging
from functools import wraps, partial
from typing import Optional, Dict, Any


class OCSAPIClient:
    """Open Chat Studio API client with timeouts and tenacity retries."""

    def __init__(self, api_key: str, base_url: str = "https://chatbots.dimagi.com", timeout_seconds: int = 300,
                 num_retries: int = 3, retry_wait_seconds: int = 2):
        """
        Initialize the OCS API client.

        Args:
            api_key (str): The OCS API key for authentication.
            base_url (str): The base URL for the API. Defaults to "https://chatbots.dimagi.com".
            timeout_seconds (int): The timeout in seconds for API requests. Defaults to 300.
            num_retries (int): The number of retries for API requests. Defaults to 3.
            retry_wait_seconds (int): The number of seconds to wait between retries. Defaults to 2.
        """

        # set parameters
        self.api_key = api_key
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.num_retries = num_retries
        self.retry_wait_seconds = retry_wait_seconds

    @staticmethod
    def retry_decorator(func):
        """
        Decorator for retrying API calls.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            bound_func = partial(func, self)
            return retry(stop=stop_after_attempt(self.num_retries),
                         wait=wait_fixed(self.retry_wait_seconds))(bound_func)(*args, **kwargs)
        return wrapper

    @retry_decorator
    def create_experiment_session(self, experiment_id, participant_id, messages=None):
        """
        Create a new experiment session.

        Args:
            experiment_id (str): The ID of the experiment.
            participant_id (str): The ID of the participant.
            messages (list): A list of messages to start the session (optional).

        Returns:
            dict: The response from the server as a JSON object.
        """

        url = f"{self.base_url}/api/sessions/"
        payload = {
            "experiment": experiment_id,
            "participant": participant_id
        }
        if messages:
            payload["messages"] = messages

        return self._execute_request("creating experiment session", "POST", url, json=payload)

    @retry_decorator
    def retrieve_experiment_session(self, session_id):
        """
        Retrieve an experiment session by its ID.

        Args:
            session_id (str): The ID of the session to retrieve.

        Returns:
            dict: The response from the server as a JSON object.
        """

        url = f"{self.base_url}/api/sessions/{session_id}/"
        return self._execute_request("retrieving experiment session", "GET", url)

    @retry_decorator
    def send_new_api_message(self, experiment_id, message, session_id=None):
        """
        Send a new message to an experiment.

        Args:
            experiment_id (str): The ID of the experiment.
            message (str): The message to send.
            session_id (str, optional): The ID of the session. Defaults to None.

        Returns:
            dict: The response from the server as a JSON object.
        """

        url = f"{self.base_url}/channels/api/{experiment_id}/incoming_message"
        payload = {
            "message": message
        }
        if session_id:
            payload["session"] = session_id

        return self._execute_request("sending new message via API", "POST", url, json=payload)

    @retry_decorator
    def list_experiments(self, cursor=None):
        """
        List all experiments.

        Args:
            cursor (str, optional): The pagination cursor value. Defaults to None.

        Returns:
            dict: The response from the server as a JSON object.
        """

        url = f"{self.base_url}/api/experiments/"
        params = {}
        if cursor:
            params["cursor"] = cursor

        return self._execute_request("listing experiments", "GET", url, params=params)

    @retry_decorator
    def retrieve_experiment(self, experiment_id):
        """
        Retrieve an experiment by its ID.

        Args:
            experiment_id (str): The ID of the experiment to retrieve.

        Returns:
            dict: The response from the server as a JSON object.
        """

        url = f"{self.base_url}/api/experiments/{experiment_id}/"

        return self._execute_request("retrieving experiment", "GET", url)

    @retry_decorator
    def download_file_content(self, file_id):
        """
        Download file content by its ID.

        Args:
            file_id (int): The ID of the file to download.

        Returns:
            bytes: The content of the file.
        """

        url = f"{self.base_url}/api/files/{file_id}/content"

        return self._execute_request("downloading file content", "GET", url)

    @retry_decorator
    def chat_completions(self, experiment_id, messages):
        """
        Send messages to the experiment and get responses.

        Args:
            experiment_id (str): The ID of the experiment.
            messages (list): A list of messages to send.

        Returns:
            dict: The response from the server as a JSON object.
        """

        url = f"{self.base_url}/api/openai/{experiment_id}/chat/completions"
        payload = {
            "messages": messages
        }

        return self._execute_request("sending messages for chat completions", "POST", url, json=payload)

    @retry_decorator
    def update_participant_data(self, participant_data):
        """
        Upsert participant data for all specified experiments in the payload.

        Args:
            participant_data (dict): The participant data to upsert.

        Returns:
            None
        """

        url = f"{self.base_url}/api/participants/"
        return self._execute_request("upserting participant data", "POST", url, json=participant_data)

    @retry_decorator
    def list_experiment_sessions(self, cursor=None, ordering=None):
        """
        List all experiment sessions.

        Args:
            cursor (str, optional): The pagination cursor value. Defaults to None.
            ordering (str, optional): The field to use when ordering the results. Defaults to None.

        Returns:
            dict: The response from the server as a JSON object.
        """

        url = f"{self.base_url}/api/sessions/"
        params = {}
        if cursor:
            params["cursor"] = cursor
        if ordering:
            params["ordering"] = ordering
    
        return self._execute_request("listing experiment sessions", "GET", url, params=params)

    def _execute_request(self, action: str, method: str, url: str, headers: Dict[str, str] = None, 
                         params: Optional[Dict[str, Any]] = None, 
                         json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an HTTP request with default headers plus logging and exceptions for error statuses.
    
        Args:
            action (str): Description of the action being performed (e.g., "listing experiment sessions").
            method (str): HTTP method to use ("GET" or "POST").
            url (str): The URL to send the request to.
            headers (Dict[str, str]): HTTP headers to include in the request.
            params (Optional[Dict[str, Any]], optional): Query parameters for the request. Defaults to None.
            json (Optional[Dict[str, Any]], optional): JSON payload for the request. Defaults to None.
    
        Returns:
            Dict[str, Any]: The response from the server as a JSON object.
    
        Raises:
            Exception: If the request fails.
        """
    
        # default headers for authorization and content type
        if headers is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
    
        response = None
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout_seconds)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=json, timeout=self.timeout_seconds)
            else:
                raise ValueError(f"Unsupported method: {method}")
    
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if response and response.status_code < 500:
                logging.warning(f"Error {action}: {e}; response content: {response.content}")
            else:
                logging.warning(f"Error {action}: {e}")
            raise
