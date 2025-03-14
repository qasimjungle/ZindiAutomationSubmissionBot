import os
import json
import subprocess

from libraries.Config import CONFIG
from libraries.logging_file import logger


class BitwardenCredentialManagement:
    """Bitwarden credential management."""

    def __init__(self):
        """Initialize and fetch credentials if a list is provided."""
        self.credentials = {}
        self.log_in_bitwarden_credential()

    def log_in_bitwarden_credential(self):
        """Ensure a fresh Bitwarden session by checking login status, logging out if needed, and then logging in."""
        try:
            email = os.getenv("BW_USERNAME", "").strip()
            password = os.getenv("BW_PASSWORD", "").strip()
            if not email or not password:
                logger.error("BW_USERNAME or BW_PASSWORD is not set in environment variables.")
                return

            # Check if already logged in
            status_output = subprocess.check_output("bw status", shell=True).decode()
            status_data = json.loads(status_output)  # Convert string to JSON

            if status_data.get("status") == "locked":
                logger.info("Bitwarden is locked. Logging out first...")
                subprocess.run("bw logout", shell=True, check=True)
                logger.info("========== Logged out from Bitwarden ==========")

            if status_data.get("status") in ["unauthenticated", "locked"]:
                # Log in with stored credentials
                logger.info("Logging into Bitwarden...")
                login_process = subprocess.run(
                    f'echo "{password}" | bw login "{email}" --raw',
                    shell=True,
                    check=True
                )

                if login_process.returncode == 0:
                    logger.info("Bitwarden login successful.")
                else:
                    logger.error("Bitwarden login failed.")
                    return  # Exit if login fails

            # Unlock and get a new session
            BW_SESSION = subprocess.check_output(
                "bw unlock --passwordenv BW_PASSWORD --raw", shell=True
            ).decode().strip()

            os.environ["BW_SESSION"] = BW_SESSION
            logger.info("Bitwarden unlocked and session stored.")

        except subprocess.CalledProcessError as e:
            logger.error(f"Bitwarden operation failed: {e}")

    def get_bitwarden_item(self, item_name):
        """Get a specific item from Bitwarden by name."""
        try:
            credential_cmd = f"bw get item '{item_name}'"
            credential_data = subprocess.check_output(credential_cmd, shell=True).decode()
            item_credentials = json.loads(credential_data)
            logger.info(f"Credential '{item_name}' loaded from Bitwarden")
            return item_credentials
        except Exception as e:
            logger.error(f"Failed to get Bitwarden item '{item_name}': {e}")
            return None

    def get_bitwarden_credentials(self,item_list ):
        """Fetch multiple items from Bitwarden."""
        for item_name in item_list:
            item_data = self.get_bitwarden_item(item_name)
            if item_data:
                self.credentials[item_name] = item_data.get("login", {})
        return self.credentials
