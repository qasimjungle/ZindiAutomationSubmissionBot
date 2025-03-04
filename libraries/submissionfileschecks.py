import os
from libraries.Config import CONFIG
from pathlib import Path
from libraries.logging_file import logger
import shutil


class SubmissionFilesChecks:
    """Define SubmissionFilesChecks  which will be used to check format"""

    def __init__(self, credential =None):
        self.credential = credential

        pass

    def is_submission_file_present(self) -> bool:
        """check if submission file present in directory or not for processing."""
        for file in os.listdir(CONFIG.ZindiCompetetionFilesPath.submission_file_folder):
            if file.endswith('.csv'):
                return True
        return False

    def check_submission_filename_format(self) -> bool:
        """
        Check if all CSV filenames in submission_folder start with a competition name from base_directory.
        Return True if submission file name format is okay, which is {competition_name}_......csv.
        Otherwise, print mismatched files and return False.
        """
        competition_names = [d.name for d in Path(CONFIG.ZindiCompetetionFilesPath.competetion_folder).iterdir() if
                             d.is_dir()]
        # Get all CSV files in submission_folder
        csv_files = list(Path(CONFIG.ZindiCompetetionFilesPath.submission_file_folder).glob("*.csv"))
        if not csv_files:
            print("No CSV Files Found")
            return False
        # Find mismatched files
        mismatched_files = [csv_file.name for csv_file in csv_files if
                            not any(csv_file.stem.startswith(name) for name in competition_names)]
        if mismatched_files:
            logger.info(f"Mismatched files: {mismatched_files}")
            return False
        return True


    def move_submission_files_to_respective_competetion_folder(self) -> bool:
        """move submission files to respective competetion folder for uploading/posting."""
        competition_dirs = [d for d in os.listdir(CONFIG.ZindiCompetetionFilesPath.competetion_folder) if
                            os.path.isdir(os.path.join(CONFIG.ZindiCompetetionFilesPath.competetion_folder, d))]
        csv_files = [f for f in os.listdir(CONFIG.ZindiCompetetionFilesPath.submission_file_folder) if
                     f.endswith('.csv')]
        for competition in competition_dirs:
            competition_dir = os.path.join(CONFIG.ZindiCompetetionFilesPath.competetion_folder, competition)
            for file in csv_files:
                if file.startswith(competition):
                    source_file = os.path.join(CONFIG.ZindiCompetetionFilesPath.submission_file_folder, file)
                    destination_file = os.path.join(competition_dir, file)
                    shutil.move(source_file, destination_file)
                    logger.info(f"Moved {file} to {destination_file}")
        return  True

    def  check_if_competetion_names_and_format_correct(self):
        """checked to see if the  given competetion names are correct."""
        pass
