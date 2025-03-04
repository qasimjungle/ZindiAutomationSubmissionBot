from libraries.Config import CONFIG
from libraries.exception import SelectedCompetitionListEmptyAfterProcessingError, SubmissionFilesNotPresentFolder, \
    IncorrectSubmissionFilesNames
from libraries.logging_file import logger
from libraries.submissionfileschecks import SubmissionFilesChecks
import os
import re
import glob

class ProcessPreparation:
    """processes."""

    def __init__(self, zindi_user):
        self.user = zindi_user
        self.submission_files_checks = SubmissionFilesChecks()

    def get_opened_competetion_names_list_make_dirs(self):
        """To get opened competitions name list"""
        open_challenge_data = self.user.get_opened_challenges(reward="all", kind="competition",
                                                              fixed_index=None, open_competetion=True)
        id_list = open_challenge_data["id"].tolist()
        parent_directory = CONFIG.ZindiCompetetionFilesPath.competetion_folder
        for folder_name in id_list:
            folder_path = os.path.join(parent_directory, str(folder_name))  # Ensure it's a string
            os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist
        logger.info(f"Created directories for {len(id_list)} IDs in {parent_directory}")

    def already_submission_files_present_in_competetion_folder(self) -> bool:
        """see if submission files .csv files are already present in competetino folder."""
        competition_folder = CONFIG.ZindiCompetetionFilesPath.competetion_folder
        already_present = False
        for subdir in os.listdir(competition_folder):
            subdir_path = os.path.join(competition_folder, subdir)
            if os.path.isdir(subdir_path):  # Check if it's a directory
                csv_files = glob.glob(os.path.join(subdir_path, "*.csv"))
                if csv_files:
                    already_present = True
        return already_present

    def submission_files_checking(self):
        """submission files checks for proper preprocessing"""
        if self.submission_files_checks.is_submission_file_present():
            logger.info("submission_file_present OKAY")
        else:
              if  self.already_submission_files_present_in_competetion_folder():
                  logger.info("submission files already present in competetion folder")
              else:
                 raise  SubmissionFilesNotPresentFolder


        if not self.already_submission_files_present_in_competetion_folder():
            if self.submission_files_checks.check_submission_filename_format():
                logger.info("submission_filename_format OkAY")
            else:
                logger.info("correct submission files name which should {competetion name from url}.....csv")
                raise IncorrectSubmissionFilesNames

            if self.submission_files_checks.move_submission_files_to_respective_competetion_folder():
                logger.info("move_submission_files_to_respective_competetion_folder for posting DONE")
            else:
                logger.info("files can not be moved unexpected error.")
        return True


    @staticmethod
    def normalize_competition_name(name):
        # Convert to lowercase
        name = name.lower()
        # Replace multiple spaces with a single space
        name = re.sub(r'\s+', ' ', name)
        # Replace spaces with hyphens
        name = name.replace(" ", "-")
        # Remove non-alphanumeric characters except hyphens
        name = re.sub(r'[^a-z0-9-]', '', name)
        return name

    def make_selected_competitions_names_correct(self) -> list:
        """check if selected competetion names are correct or not."""
        selected_competition_list_corrected = []
        selected_competetion_list = CONFIG.INPUTS.selected_competetion_names_to_work
        open_challenge_data = self.user.get_opened_challenges(reward="all", kind="competition",
                                                              fixed_index=None, open_competetion=True)
        id_list = open_challenge_data["id"].tolist()
        for selected_competetion in selected_competetion_list:
            if selected_competetion in id_list:
                normalized_competetion_name = self.normalize_competition_name(selected_competetion)
                if normalized_competetion_name in id_list:
                    selected_competition_list_corrected.append(normalized_competetion_name)
                else:
                    logger.info(f"Competetion name is incorrect {selected_competetion}")
                    logger.info("removing it from selected competetion list")
        return selected_competition_list_corrected

    def keep_selected_competitions_which_open_competition(self,selected_competition_list: list) -> list:
        """ To check if selected competetion selected or not."""
        removed_competetion_which_are_closed = []
        open_challenge_data = self.user.get_opened_challenges(reward="all", kind="competition",
                                                              fixed_index=None, open_competetion=True)
        id_list = open_challenge_data["id"].tolist()
        for selected_competition in selected_competition_list:
            if selected_competition in id_list:
                removed_competetion_which_are_closed.append(selected_competition)
            else:
                logger.info(f"Competetion names is not opened {selected_competition}")
                logger.info(f"Removing competition from selected list {selected_competition}")
        return removed_competetion_which_are_closed


    def keep_selected_competitions_submission_limit_not_reach(self,selected_competition_list:list ) -> list:
        """ Check if  selected competetion has already read it limit of submissions."""
        selected_competition_removed_submission_limit_reached = []
        for selected_challenge in selected_competition_list:
            daily_remaining_submission_data = self.user.availabel_remaining_submission_for_selected_competetion(
                selected_challenge)
            today_remaining = daily_remaining_submission_data['data']['today']
            already_submitted = daily_remaining_submission_data['data']['submitted_today']
            temporary = ""
            if temporary==False:
                logger.info(f"removing competition  {selected_challenge} submission already reach it limit")
            else:
                    selected_competition_removed_submission_limit_reached.append(selected_challenge)
        return selected_competition_removed_submission_limit_reached


    def check_if_selected_competetion_list_not_empty(self,selected_competition_list:list) -> None:
        """see if  competition list is not empty."""
        if selected_competition_list:
            pass
        else:
          raise SelectedCompetitionListEmptyAfterProcessingError