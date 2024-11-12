# colab_local_env.py - Tools for working with Google Colab and local development environments

import os
import sys
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import dotenv
from dataclasses import dataclass
import requests


@dataclass
class ColabOrLocalEnv:
    """
    Environment handler that works in both Google Colab and local development.

    Args:
        github_repo: Repository in format "username/repo"
        github_branch: Branch to use (default: "main")
        requirements_path: Optional relative path to requirements.txt within repo
        module_paths: Optional list of relative paths to Python modules to fetch in Colab
        secrets_path: Optional full path to secrets file (only used locally)
        secrets_template: Optional dict of secret names and default values
    """

    github_repo: str
    github_branch: str = "main"
    requirements_path: Optional[str] = None
    module_paths: Optional[List[str]] = None
    secrets_path: Optional[str] = None
    secrets_template: Optional[Dict[str, str]] = None

    _is_colab: bool = False
    _config_loaded: bool = False
    _dependencies_installed: bool = False
    _modules_fetched: bool = False

    def __post_init__(self):
        """Detect environment and initialize configuration."""

        # Detect if we're running in Colab
        try:
            # noinspection PyPackageRequirements
            from google.colab import userdata   # type: ignore[import]
            self._is_colab = True
            self._userdata = userdata
        except ImportError:
            self._is_colab = False

        # If we have secrets config, load it when running locally
        if not self._is_colab and self.secrets_path:
            self._load_config()

    def _load_config(self) -> None:
        """Load configuration from secrets file when running locally."""
        if self._config_loaded or not self.secrets_path:
            return

        # Expand user directory if needed
        config_path = Path(os.path.expanduser(self.secrets_path))

        # Create parent directories if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if not config_path.exists():
            if self.secrets_template:
                # Create template secrets file
                template = ""
                for key, value in self.secrets_template.items():
                    template += f"{key}={value}\n"
                config_path.write_text(template)

            raise Exception(f"Please configure your settings in {config_path}")

        if config_path.exists():
            dotenv.load_dotenv(config_path)
            self._config_loaded = True

    def _get_github_raw_url(self, path: str) -> str:
        """Convert a repository path to a raw GitHub URL."""
        return f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_branch}/{path}"

    def setup_environment(self) -> None:
        """
        Set up the environment by installing dependencies and fetching source files.
        Should be called before any other operations.
        """
        self._install_dependencies()
        if self._is_colab and self.module_paths:
            self._fetch_modules()

    def _install_dependencies(self) -> None:
        """Install required dependencies from requirements.txt if specified."""
        if self._dependencies_installed or not self.requirements_path:
            return

        try:
            if self._is_colab:
                # Fetch requirements.txt from GitHub
                req_url = self._get_github_raw_url(self.requirements_path)
                response = requests.get(req_url)
                response.raise_for_status()

                # Write requirements to a temporary file
                req_path = Path("/content/requirements.txt")
                req_path.write_text(response.text)
            else:
                # Find project root and use relative path from there
                project_root = self._find_project_root()
                if not project_root:
                    raise FileNotFoundError("Could not find project root directory")

                req_path = project_root / self.requirements_path
                if not req_path.exists():
                    raise FileNotFoundError(f"Requirements file not found at {req_path}")

            # Install requirements
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])
            self._dependencies_installed = True
            print("Dependencies installed successfully.")

        except Exception as e:
            raise Exception(f"Failed to install dependencies: {str(e)}")

    def _fetch_modules(self) -> None:
        """Fetch required Python modules from GitHub when running in Colab."""
        if not self._is_colab or not self.module_paths or self._modules_fetched:
            return

        for module_path in self.module_paths:
            try:
                # Fetch module from GitHub
                module_url = self._get_github_raw_url(module_path)
                response = requests.get(module_url)
                response.raise_for_status()

                # Determine the output path in Colab
                output_path = Path("/content") / Path(module_path).name
                output_path.write_text(response.text)
                print(f"Downloaded {module_path}")

            except Exception as e:
                raise Exception(f"Failed to fetch {module_path}: {str(e)}")

        # Add /content to Python path so imported modules can be found
        if str(Path("/content")) not in sys.path:
            sys.path.insert(0, str(Path("/content")))

        self._modules_fetched = True

    def get_secret(self, secret_name: str, default_value: Any = None) -> Any:
        """Get a secret from Colab userdata or local environment variables."""
        if self._is_colab:
            # noinspection PyBroadException
            try:
                return self._userdata.get(secret_name)
            except Exception:
                return default_value
        else:
            return os.getenv(secret_name.upper(), default_value)

    def get_working_dir(self) -> Path:
        """Get the working directory (where files are processed)."""
        return Path("/content") if self._is_colab else Path.cwd()

    def _find_project_root(self) -> Optional[Path]:
        """
        Find the project root directory by looking for common project markers.
        Starts from the current working directory and moves up until a marker is found.
        """
        # Common files that indicate project root
        project_markers = [
            self.requirements_path,  # The requirements.txt path we were given
            "pyproject.toml",
            "setup.py",
            ".git",
            ".gitignore",
            "README.md"
        ]

        current = Path.cwd().resolve()

        # Keep going up until we find a marker or hit the root
        while current != current.parent:
            # Check each marker
            for marker in project_markers:
                if (current / marker).exists():
                    return current

            # Move up one directory
            current = current.parent

        return None

    def get_input_files(self, file_chooser_title: str) -> List[str]:
        """
        Get list of input files, either via Colab upload or local file selection.
        Returns: List of Path objects pointing to the input files
        """
        if self._is_colab:
            from IPython.display import display, HTML
            display(HTML(f"<h3>{file_chooser_title}</h3>"))
            # noinspection PyPackageRequirements
            from google.colab import files  # type: ignore[import]
            uploaded = files.upload()
            content_dir = Path("/content")
            return [content_dir / filename for filename in uploaded.keys()]
        else:
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            file_paths = filedialog.askopenfilenames(
                title=file_chooser_title
            )

            return [str(path) for path in file_paths]

    @property
    def is_colab(self) -> bool:
        """Return whether we're running in Colab."""
        return self._is_colab
