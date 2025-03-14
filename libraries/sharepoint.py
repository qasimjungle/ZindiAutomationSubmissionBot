""" This module contains all the functions related to SharePoint. """

import os
import shutil
import urllib
from datetime import datetime
from pathlib import Path
from typing import List
from urllib.parse import quote, unquote

import numpy as np
import pandas as pd
import pytz
import requests
import simplejson as json
from O365 import Account
from requests.exceptions import JSONDecodeError
from retry import retry
from t_bug_catcher import report_error
from t_office_365 import OfficeAccount

from config import CONFIG, BugCatcher
from libraries import logger
from libraries.exceptions import FileWasNotDownloadedException, FolderNotFoundError, SharePointFileLockedException


class SharePoint:
    def __init__(self, credentials: dict):
        self.main_endpoint = "https://graph.microsoft.com/v1.0"
        self.host_name = "proliancesurgeons.sharepoint.com"
        self.tenant_id = credentials["Directory (tenant) ID"]
        self.client_id = credentials["Application (client) ID"]
        self.client_secret = credentials["Client Secret Value"]
        self.login = credentials["login"]
        self.folder_to_save_files = CONFIG.DIRECTORIES.MAPPING
        self.expiration_datetime = datetime.now()
        self._site_url = "%s/sites/%s:/sites/Thoughtful-AI"  # main_endpoint, host_name
        self.site_id = ""
        self.access_token = ""
        self.drive_id = ""

        self.office = OfficeAccount(
            client_id=self.client_id,
            client_secret=self.client_secret,
            tenant_id=self.tenant_id,
            main_resource=self.login,
        )
        self.sp = self.office.sharepoint.site(site_name="sites/Thoughtful-AI")

        self.authenticate_and_get_drive_id()

    def relogin_sp(self):
        """
        This method re-authenticates the O365 account and gets the drive id.
        """
        self.office = OfficeAccount(
            client_id=self.client_id,
            client_secret=self.client_secret,
            tenant_id=self.tenant_id,
            main_resource=self.login,
        )
        self.sp = self.office.sharepoint.site(site_name="sites/Thoughtful-AI")

    def authenticate_and_get_drive_id(self):
        """
        This method authenticates the O365 account and gets the drive id.
        """
        self.access_token = self.authenticate_account()
        self.site_id = self.get_site_id(self.access_token)
        drive_info = self.get_site_drive_info(self.site_id, self.access_token)
        self.drive_id = drive_info["id"]

    @retry(tries=3, delay=2, backoff=2)
    def authenticate_account(self) -> str:
        """
        The function authenticates an O365 account using Microsoft Graph and
        returns the access token.
        :return: the access token obtained from the authentication process.
        """
        logger.info("Begin O365 Account Authentication via Microsoft Graph")
        credentials = (self.client_id, self.client_secret)
        try:
            account = Account(credentials, auth_flow_type="credentials", tenant_id=self.tenant_id)
            account.authenticate()
            if account.connection.token_backend.token is not None:
                self.expiration_datetime = account.connection.token_backend.token.expiration_datetime
            else:
                logger.error("Token not generated, authentication might have failed.")
                raise Exception("Token generation failed during authentication")
            with open("o365_token.txt") as f:
                data = f.read()
                js = json.loads(data)
                access_token = js["access_token"]
                logger.info("Authenticated!")
                return access_token
        except Exception as ex:
            logger.error(f"Authentication Failed: {ex}")
            raise ex

    def get_site_id(self, access_token: str) -> str:
        """
        The function retrieves the site ID for a given host name using an access token.

        :param access_token: The access_token parameter is a token that is used to authenticate the user
        and authorize access to the API. It is typically obtained by the user through an authentication
        process
        :return: the site ID.
        """
        try:
            result = requests.get(
                self._site_url % (self.main_endpoint, self.host_name),
                headers={"Authorization": "Bearer " + access_token},
            )
            site_info = result.json()
            site_id = site_info["id"]
            logger.info("Get Site ID Success.")
            return site_id
        except Exception as ex:
            logger.info(f"Getting Site ID Failed: {ex}")
            raise ex

    def get_site_drive_info(self, site_id: str, access_token: str) -> dict:
        """
        The function retrieves drive information for a specific site using the
        site ID and access token.

        :param site_id: The site_id parameter is the unique identifier for a specific site or location.
        It is used to specify which site's drive information should be retrieved
        :param access_token: The access_token parameter is a token that is used to authenticate the user
        and authorize access to the Microsoft Graph API. It is typically obtained by the user logging in
        and granting permission to the application to access their data
        :return: the drive information for a specific site.
        """
        try:
            result = requests.get(
                f"{self.main_endpoint}/sites/{site_id}/drive", headers={"Authorization": "Bearer " + access_token}
            )
            return result.json()
        except Exception as ex:
            logger.error(f"Getting Drive Info Failed: {ex}")
            raise ex

    def get_mapping_files_folder_contents(self, folder_id: str, drive_id: str, access_token: str) -> list:
        """
        The function retrieves the contents of a specified folder in a drive using the Microsoft Graph
        API.

        :param folder_id: The folder_id parameter is the unique identifier of the folder whose contents
        you want to retrieve
        :param drive_id: The `drive_id` parameter is the unique identifier of the drive where the folder
        is located. It specifies the drive from which to retrieve the folder's children
        :param access_token: The access_token parameter is a token that is used to authenticate and
        authorize the user's access to the Microsoft Graph API. It is obtained through the
        authentication process and is required to make requests to the API
        :return: the list of children items in the specified folder.
        """
        logger.info("Begin Get Mapping Files Children Info")
        try:
            result = requests.get(
                f"{self.main_endpoint}/drives/{drive_id}/items/{folder_id}/children",
                headers={"Authorization": "Bearer " + access_token},
            )
            children = result.json()["value"]
        except Exception as ex:
            logger.error(f"Get Mapping Files Children Failed: {ex}")
            raise ex
        finally:
            logger.info("Get Mapping Files Children Success.")
            return children

    @retry(exceptions=(JSONDecodeError,), tries=3)
    def get_file_info(self, file_name: str) -> dict:
        """
        The function retrieves information about a file from a specified drive using the
        Microsoft Graph API.
        Args:
            file_name (str): The name of the file you want to retrieve from the drive
        """
        try:
            file_path = f"{file_name}"
            file_url = urllib.parse.quote(file_path)
            result = requests.get(
                f"{self.main_endpoint}/drives/{self.drive_id}/root:/{file_url}",
                headers={"Authorization": "Bearer " + self.access_token},
            )
            file_info = result.json()
            return file_info
        except JSONDecodeError as json_ex:
            logger.info(f"JSON Decode Error: {json_ex} for file: {file_path}")
            raise json_ex
        except Exception as ex:
            logger.info(f"Get File ID Failed: {ex}")
            raise ex

    def get_mapping_file(self, file_id: str, file_name: str, folder_to_save_files: str) -> None:
        """
        The function retrieves a file from a specified drive and saves it to the local file system.
        Args:
            file_id: The ID of the file you want to retrieve. This is typically a unique identifier
            assigned to each file in the storage system you are using (e.g., Google Drive, Dropbox, etc.)
            file_name: The name of the file you want to retrieve from the drive
            folder_to_save_files: The folder path where the file will be saved
        """
        try:
            result = requests.get(
                f"{self.main_endpoint}/drives/{self.drive_id}/items/{file_id}/content",
                headers={"Authorization": "Bearer " + self.access_token},
            )

            # Define the full path for the Excel file
            file_path = os.path.join(folder_to_save_files, Path(file_name).name)

            if os.path.exists(file_path):
                os.remove(file_path)

            # create a new file with create and write params
            with open(file_path, "wb") as f:
                f.write(result.content)
            logger.info(f"File '{file_path}' downloaded successfully.")
        except Exception as ex:
            logger.error(f"Get {file_name} File Failed: {ex}")
            raise ex

    def get_file(self, file_id: str, file_name: str, dest_folder_path: str) -> str:
        """
        The function retrieves a file from a specified drive and saves it to the local file
        system.
        Args:
            file_id: The ID of the file you want to retrieve. This is typically a unique identifier
            assigned to each file in the storage system you are using (e.g., Google Drive, Dropbox, etc.)
            file_name: The name of the file you want to retrieve from the drive
            dest_folder_path: The destination folder path
        Returns:
            str: The file path of the downloaded file
        """
        try:
            logger.info("Begin Get File")
            result = requests.get(
                f"{self.main_endpoint}/drives/{self.drive_id}/items/{file_id}/content",
                headers={"Authorization": "Bearer " + self.access_token},
            )

            # Define the full path for the Excel file
            file_path = os.path.join(dest_folder_path, file_name)
            Path(dest_folder_path).mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(result.content)
            logger.info(f"File downloaded to {file_path}")
            return file_path
        except Exception as ex:
            logger.error(f"Get File Failed: {ex} - {file_name}")
            raise ex

    @retry(tries=3, delay=10, backoff=5)
    def download_mapping_files(self, files: list, folder_to_save_files: str = CONFIG.DIRECTORIES.MAPPING):
        """
        The function downloads mapping files from a SharePoint drive.
        Args:
            files: The SharePoint file path
            folder_to_save_files: The destination folder path
        """
        Path(folder_to_save_files).mkdir(parents=True, exist_ok=True)

        self.check_and_update_token()

        for file_name in files:
            file_info = self.get_file_info(file_name)
            self.get_mapping_file(file_info["id"], file_name, folder_to_save_files)

    def download_file(self, sharepoint_file_path: str, dest_folder_path: str, dest_file_name: str = "") -> str:
        """
        The function `download_file` downloads a file from a SharePoint drive.
        Args:
            sharepoint_file_path: The SharePoint file path
            dest_folder_path: The destination folder path
            dest_file_name: The destination file name
        Returns:
            str: The file path of the downloaded file
        """
        try:
            logger.info(f"Begin Download File: '{sharepoint_file_path}'")
            self.check_and_update_token()

            file_info = self.get_file_info(sharepoint_file_path)
            if error := file_info.get("error", ""):
                raise FileWasNotDownloadedException(error.get("message", "Unknown Error"))
            if not dest_file_name:
                dest_file_name = file_info["name"]
            return self.get_file(file_info["id"], dest_file_name, dest_folder_path)
        except Exception as ex:
            logger.error(f"Download File Failed: {ex}")
            report_error(exception=ex, assignee=BugCatcher.DEFAULT_ASSIGNEE)
            return ""

    def file_exists(self, file_path: str) -> bool:
        """
        This method checks if a file exists in a SharePoint drive.
        Args:
            file_path (str): file path to check
        Returns:
            bool: True if the file exists, False otherwise
        """
        self.check_and_update_token()

        file_info = self.get_file_info(file_path)
        if "error" in file_info:
            return False
        return True

    def upload_file(self, file_path: str, folder_path: str, file_name: str = ""):
        """
        This method uploads a file to a specified folder in a SharePoint drive.
        Args:
            file_path (_type_): file path to upload
            folder_path (_type_): folder path to upload to
            file_name (_type_): file name to upload
        """
        try:
            st = os.stat(file_path)
            size = st.st_size

            self.check_and_update_token()

            folder_id_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{quote(folder_path)}"
            folder_id = self.get_folder_id(folder_id_endpoint, True)
            file_name = file_name if file_name else os.path.basename(file_path)
            path_url = quote(f"{folder_path}") + f"/{file_name}"

            if size / (1024 * 1024) < 4:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                file_info_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{path_url}"
                result = requests.get(file_info_endpoint.format(file_path=path_url), headers=headers)
                if result.status_code == 200:
                    logger.info("file exists, replace its contents")
                    file_info = result.json()
                    self.__upload_existing_file_by_id(file_path, file_info["id"])
                elif result.status_code == 404:
                    logger.info("file does not exist, create a new item")
                    self.__upload_not_existing_file_by_folder_id(file_path, file_name, folder_id)
            else:
                # TODO: - Can fail. Should be tested
                self.__upload_large_file(file_path, file_name, folder_id, size)
            logger.info(f"File uploaded successfully. {file_name} to {folder_path}")
        except FolderNotFoundError as e:
            logger.error(f"Could not upload file {file_name}, - {str(e)}")
            try:
                shutil.copyfile(file_path, os.path.join(self.folder_to_save_files, os.path.basename(file_path)))
            except shutil.SameFileError:
                pass
        except Exception as e:
            logger.error(f"Could not upload file {file_name}, - {str(e)}")
            report_error(exception=e, assignee=BugCatcher.DEFAULT_ASSIGNEE)
            try:
                shutil.copyfile(file_path, os.path.join(self.folder_to_save_files, os.path.basename(file_path)))
            except shutil.SameFileError:
                pass

    @retry(tries=3, delay=10, backoff=2)
    def __upload_existing_file_by_id(self, file_path, file_id):
        """
        This method uploads a file to a specified folder in a SharePoint drive. It overwrites the existing file.
        Args:
            file_path (_type_): file path of the file to upload
            file_id (_type_): file id of the file to upload
        Raises:
            SharePointFileLockedError: exception raised when the file is locked
        """
        self.check_and_update_token()

        file_content_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/items/{file_id}/content"
        with open(file_path, "rb") as f:
            data = f.read()
            result = requests.put(
                file_content_endpoint,
                headers={"Authorization": "Bearer " + self.access_token, "Content-type": "application/binary"},
                data=data,
            )
        if result.status_code == 423:
            raise SharePointFileLockedException(f"File {os.path.basename(file_path)} locked!")
        result.raise_for_status()

    @retry(tries=3, delay=10, backoff=2)
    def __upload_not_existing_file_by_folder_id(self, file_path: str, file_name: str, folder_id: str):
        """
        This method uploads a file to a specified folder in a SharePoint drive.
        It retries in case of a 504 Gateway Timeout.
        Args:
            file_path (str): file path of the file to upload
            file_name (str): file name of the file to upload
            folder_id (str): folder id of the folder to upload to
        Raises:
            SharePointFileLockedError: exception raised when the file is locked
        """
        self.check_and_update_token()

        file_content_url = f"{self.main_endpoint}/drives/{self.drive_id}/items/{folder_id}:/{quote(file_name)}:/content"

        file_size = os.path.getsize(file_path)

        result = requests.put(
            file_content_url,
            headers={"Authorization": "Bearer " + self.access_token, "Content-type": "application/binary"},
            data=open(file_path, "rb").read(),
            timeout=120,
        )

        if result.status_code == 423:
            raise SharePointFileLockedException(f"File {file_name} locked!")

        if result.status_code == 504 and file_size > 4 * 1024 * 1024:
            raise requests.exceptions.HTTPError(
                f"504 Gateway Timeout while uploading {file_name}. "
                f"The file size is {file_size / (1024 * 1024):.2f} MB, "
                f"which exceeds 4 MB. This may cause timeouts. Consider using chunked upload."
            )
        elif result.status_code == 504:
            raise requests.exceptions.HTTPError(f"504 Gateway Timeout while uploading {file_name}.")

        if result.status_code == 404:
            raise requests.exceptions.HTTPError(f"404 Not Found: Folder or file not found at {file_content_url}")

        result.raise_for_status()

    def check_and_update_token(self):
        """
        This method checks if the token is expired and updates it if it is.
        """
        tz = pytz.timezone("US/Central")
        if self.expiration_datetime.astimezone(tz) < datetime.now(tz=tz):
            logger.info("Token expired. Updating token...")
            self.authenticate_and_get_drive_id()

    @retry(tries=3, backoff=5)
    def get_folder_id(self, folder_endpoint: str, create_if_not_exist: bool = False) -> str:
        """
        This method gets the folder id from a folder endpoint.
        Args:
            folder_endpoint (str): folder endpoint
            create_if_not_exist (bool): create folder if it does not exist
        Returns:
            str: folder id
        """
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(folder_endpoint, headers=headers)
            result.raise_for_status()
            return result.json()["id"]
        except requests.HTTPError as ex:
            if ex.response.status_code == 404:
                folder_endpoint = unquote(folder_endpoint)
                logger.info(f"Folder not found at endpoint: {folder_endpoint} ")
                if create_if_not_exist:
                    # 1 - Decode folder_endpoint using unquote to ensure proper handling of any URL-encoded characters.
                    # 2 - Split the path into its components to make the path
                    # 3 - Create the necessary folder along the path.
                    # 4 - Raise an exception to force a retry when getting the folder ID.

                    folder_path, folder = os.path.split(folder_endpoint)
                    root = folder_endpoint.find("root:") + 5
                    self.create_new_folder(folder_name=folder, folder_path=folder_path[root:])
                    raise FolderNotFoundError("Forcing get_folder_id to reload...")
                else:
                    logger.info("Returning folder_id None.")
                    return None
            else:
                raise ex
        except Exception as ex:
            raise ex

    def __upload_large_file(self, file_path: str, file_name: str, folder_id: str, size: int):
        """
        This method uploads a large file to a specified folder in a SharePoint drive.
        Args:
            file_path (str): file path of the file to upload
            file_name (str): file name of the file to upload
            folder_id (str): folder id
            size (int): size of the file to upload
        Raises:
            SharePointFileLockedError: exception raised when the file is locked
        """
        result = requests.post(
            self.file_upload_session_endpoint.format(folder_id=folder_id, file_url=self.encode_url(file_name)),
            headers=self.headers,
            json={
                "@microsoft.graph.conflictBehavior": "replace",
                "description": "A large file",
                "fileSystemInfo": {"@odata.type": "microsoft.graph.fileSystemInfo"},
                "name": file_path,
            },
        )
        if result.status_code == 423:
            raise SharePointFileLockedException(f"File {file_name} locked!")
        result.raise_for_status()
        upload_url = result.json()["uploadUrl"]

        chunks = int(size / self.file_chunk_size) + 1 if size % self.file_chunk_size > 0 else 0
        with open(file_path, "rb") as fd:
            start = 0
            for chunk_num in range(chunks):
                chunk = fd.read(self.file_chunk_size)
                bytes_read = len(chunk)
                upload_range = f"bytes {start}-{start + bytes_read - 1}/{size}"
                logger.info(f"chunk: {chunk_num} bytes read: {bytes_read} upload range: {upload_range}")
                result = requests.put(
                    upload_url, headers={"Content-Length": str(bytes_read), "Content-Range": upload_range}, data=chunk
                )
                result.raise_for_status()
                start += bytes_read

    def folder_exists(self, folder_path: str) -> bool:
        """
        This method checks if a folder exists in a SharePoint drive.
        Args:
            folder_path (str): folder path to check
        Returns:
            bool: True if the folder exists, False otherwise
        """
        self.check_and_update_token()

        folder_id_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{quote(folder_path)}"
        try:
            folder_id = self.get_folder_id(folder_id_endpoint)
            if folder_id:
                logger.info(f"Folder '{folder_path}' exists in SharePoint.")
                return True
            else:
                logger.info(f"Folder '{folder_path}' does not exist in SharePoint.")
                return False
        except Exception as ex:
            report_error(exception=ex, assignee=BugCatcher.DEFAULT_ASSIGNEE)
            logger.error(f"An unexpected error occurred while checking folder existence: {ex}")
            return False

    @retry(tries=3, delay=3, backoff=2)
    def create_new_folder(self, folder_name: str, folder_path: str) -> None:
        """
        This method creates a new folder in a SharePoint drive.
        Args:
            folder_name (str): name of the folder to create
            folder_path (str): name of the folder where the new folder will be created
        """
        self.check_and_update_token()

        folder_id_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{quote(folder_path)}"
        folder_id = self.get_folder_id(folder_id_endpoint)
        url = f"{self.main_endpoint}/sites/{self.site_id}/drive/items/{folder_id}/children"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {"name": folder_name, "folder": {}, "@microsoft.graph.conflictBehavior": "replace"}
        try:
            requests.post(url, headers=headers, json=payload)
            logger.info(f"Folder {quote(folder_name)} created successfully.")
        except Exception as ex:
            logger.error(f"Create New Folder Failed: {ex}")
            raise ex

    def upload_folder(self, source_folder: str, destination_path: str, new_folder: str) -> None:
        """
        This method uploads a folder in a SharePoint drive.
        Args:
            source_folder (str): source folder to upload
            destination_path (str): destination path where the folder will be uploaded
            new_folder (str): base source folder
        """
        logger.info(f"Uploading folder {source_folder} to {quote(destination_path)}/{new_folder}")

        self.check_and_update_token()

        folder_id_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{quote(destination_path)}/{new_folder}"
        final_path = os.path.join(destination_path, new_folder)
        try:
            self.get_folder_id(folder_id_endpoint)
        except Exception as e:
            report_error(exception=e, assignee=BugCatcher.DEFAULT_ASSIGNEE)
            logger.info(">> Folder does not exist. Creating it...")
            self.create_new_folder(new_folder, destination_path)
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                logger.info(f">> Uploading file {file} to {quote(final_path)}")
                file_path = os.path.join(root, file)
                self.upload_file(file_path, final_path)

    def delete_all_files_in_folder(self, folder_path: str) -> None:
        """
        This method deletes all files from a specified folder in a SharePoint drive.
        Args:
            folder_path (str): folder path to delete files from
        """
        self.check_and_update_token()

        folder_id_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{quote(folder_path)}"
        try:
            folder_id = self.get_folder_id(folder_id_endpoint)
            files_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/items/{folder_id}/children"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(files_endpoint, headers=headers)
            result.raise_for_status()
            files = result.json().get("value", [])
            for file in files:
                file_id = file.get("id")
                file_name = file.get("name")
                file_delete_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/items/{file_id}"
                requests.delete(file_delete_endpoint, headers=headers)
                logger.info(f"Deleted file: {file_name}")
            logger.info(f"All files deleted from folder: {folder_path}")
        except Exception as ex:
            logger.error(f"Delete Files Failed: {ex}")
            raise ex

    def delete_files_in_folder_that_starts_with(self, folder_path: str, starts_with: str) -> None:
        """
        This method deletes all files from a specified folder in a SharePoint drive that start with a specified string.
        Args:
            folder_path (str): folder path to delete files from
            starts_with (str): string that the file name should start with
        """
        logger.info(f"Deleting files from folder: {folder_path} that start with: {starts_with}")
        self.check_and_update_token()

        folder_id_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{quote(folder_path)}"
        try:
            folder_id = self.get_folder_id(folder_id_endpoint)
            files_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/items/{folder_id}/children"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(files_endpoint, headers=headers)
            result.raise_for_status()
            files = result.json().get("value", [])
            for file in files:
                file_id = file.get("id")
                file_name = file.get("name")
                if file_name.startswith(starts_with):
                    file_delete_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/items/{file_id}"
                    requests.delete(file_delete_endpoint, headers=headers)
                    logger.info(f"Deleted file: {file_name}")
            logger.info(f"All files deleted from folder: {folder_path} that start with: {starts_with}")
        except Exception as ex:
            logger.error(f"Delete Files Failed: {ex}")
            raise ex

    def delete_all_files_in_folder_older_than_2_days(self, folder_path: str) -> None:
        """
        This method deletes all files older than 2 days from a specified folder in a SharePoint drive.
        Args:
            folder_path (str): folder path to delete files from
        """
        self.check_and_update_token()

        folder_id_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{quote(folder_path)}"
        try:
            folder_id = self.get_folder_id(folder_id_endpoint)
            files_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/items/{folder_id}/children"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(files_endpoint, headers=headers)
            result.raise_for_status()
            files = result.json().get("value", [])
            for file in files:
                file_id = file.get("id")
                file_name = file.get("name")
                file_created_date = file.get("createdDateTime")
                file_created_date = datetime.strptime(file_created_date, "%Y-%m-%dT%H:%M:%SZ")
                if (datetime.now() - file_created_date).days > 2:
                    file_delete_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/items/{file_id}"
                    requests.delete(file_delete_endpoint, headers=headers)
                    logger.info(f"Deleted file: {file_name}")
                else:
                    logger.info(f"File: {file_name} is not older than 2 days.")

            logger.info(f"All files older than 2 days deleted from folder: {folder_path}")
        except Exception as ex:
            logger.error(f"Delete Files Older Than 2 Days Failed: {ex}")
            raise ex

    def download_all_files_from_folder_that_starts_with(
        self, folder_path: str, starts_with: str, dest_folder_path: str
    ):
        """
        This method downloads all files from a specified folder in a SharePoint drive that start with a specif string.
        Args:
            folder_path (str): folder path to download files from
            starts_with (str): string that the file name should start with
            dest_folder_path (str): destination folder path
        """
        self.check_and_update_token()

        folder_id_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/root:/{quote(folder_path)}"
        try:
            folder_id = self.get_folder_id(folder_id_endpoint)
            files_endpoint = f"{self.main_endpoint}/drives/{self.drive_id}/items/{folder_id}/children"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(files_endpoint, headers=headers)
            result.raise_for_status()
            result.raise_for_status()
            files = result.json().get("value", [])
            for file in files:
                file_id = file.get("id")
                file_name = file.get("name")
                if file_name.startswith(starts_with):
                    self.get_file(file_id, file_name, dest_folder_path)
                    logger.info(f"Downloaded file: {file_name}")
            logger.info(f"All files downloaded from folder: {folder_path} that start with: {starts_with}")
        except Exception as ex:
            logger.error(f"Download Files Failed: {ex}")
            raise ex

    @retry(tries=5, delay=3, backoff=2)
    def update_row_values_with_retry(
        self, file_id: str, sheet_name: str, values: list, row: int, verify_update: bool = False
    ) -> None:
        self.sp.excel.update_row_values(
            file_id,
            sheet_name,
            values=values,
            row=row,
        )
        col_to_check = CONFIG.PaymentMaster.Columns.FILE_COL_INDEX
        if verify_update:
            updated_values = self.sp.excel.get_row_values(file_id, sheet_name, row)
            if updated_values[col_to_check] != values[col_to_check]:
                logger.error(f"Row values were not updated correctly. Expected: {values}, Actual: {updated_values}")
                raise Exception("Row values were not updated correctly.")

    def update_live(
        self,
        path: str,
        new_df: pd.DataFrame,
        matching_col_name: str,
        filter_columns_name: List[str] = None,
        sheet_name: str = "Sheet1",
    ):
        """
        This method updates the file in SharePoint.
        """
        logger.info(f"Updating file: {path}")
        if not self.office.sharepoint.account.is_authenticated:
            self.office.sharepoint.account.authenticate()
        file_id = self.sp.get_file_id_by_path(path)
        data = self.sp.excel.get_rows_values(file_id, sheet_name)
        df = pd.DataFrame(data[1:], columns=data[0])
        df[matching_col_name] = df[matching_col_name].astype(str)
        data_len = len(data)

        new_df.replace([np.inf, -np.inf, np.nan], "", inplace=True)

        for i, row in new_df.iterrows():
            try:
                matching_value = row[matching_col_name].strip("'")
                if matching_value in df[matching_col_name].values:
                    existing_row = df[df[matching_col_name] == matching_value]
                    if filter_columns_name:
                        existing_filter_values = [existing_row[col].values[0] for col in filter_columns_name]
                        new_filter_values = [row[col].strip("'") for col in filter_columns_name]
                        if existing_filter_values and all(
                            value in new_filter_values and value for value in existing_filter_values
                        ):
                            logger.info(f"Row already processed. Skipping: {matching_value}")
                            continue
                    self.update_row_values_with_retry(
                        file_id,
                        sheet_name,
                        values=row.to_list(),
                        row=existing_row.index[0] + 2,
                        verify_update=True,
                    )
                    logger.info(f"Updated payment row: {matching_value}")
                    logger.debug(f"Updated payment row: {row.to_list()}")
                else:
                    data_len += 1
                    row_index = data_len
                    self.update_row_values_with_retry(
                        file_id, sheet_name, values=row.to_list(), row=row_index, verify_update=True
                    )
                    logger.info(f"Added payment row: {matching_value} at index {row_index}")
                    logger.debug(f"Added payment row: {row.to_list()} at index {row_index}")
            except Exception as e:
                logger.error(f"Failed to update/add row: {row.to_list()}, {e}")
                report_error(exception=e, assignee=BugCatcher.DEFAULT_ASSIGNEE)

    @retry(tries=3, delay=3)
    def read_file_live(self, path: str, sheet_name: str = "Sheet1") -> pd.DataFrame:
        """
        This method reads the file in SharePoint.
        """
        logger.info(f"Reading file: {path}")
        if not self.office.sharepoint.account.is_authenticated:
            self.office.sharepoint.account.authenticate()
        file_id = self.sp.get_file_id_by_path(path)
        data = self.sp.excel.get_rows_values(file_id, sheet_name)
        return pd.DataFrame(data[1:], columns=data[0])

    def rewrite_live(self, path: str, new_df: pd.DataFrame, sheet_name: str = "Sheet1"):
        """
        This method rewrites the file in SharePoint.
        """
        logger.info(f"Rewriting file: {path}")
        if not self.office.sharepoint.account.is_authenticated:
            self.office.sharepoint.account.authenticate()
        file_id = self.sp.get_file_id_by_path(path)
        for i, row in new_df.iterrows():
            self.update_row_values_with_retry(file_id, sheet_name, values=row.to_list(), row=int(i) + 2)