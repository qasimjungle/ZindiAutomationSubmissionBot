import os
import shutil
from libraries.Config import CONFIG
from libraries.logging_file import logger
from libraries.zindi.user import Zindian
import pandas as pd

class ZindiProcessing:
    """Automation of zindi site."""

    def __init__(self,user, credentials, show_leaderboard, show_rank,
                 upload_submission_file, download_dataset, daily_submission_remaining,report_dataframe):
        self.credentials = credentials
        self.credential = credentials
        self.print_leader_board_for_selected_competetion = show_leaderboard
        self.print_user_rank_for_selected_competetion = show_rank
        self.submit_submission_file_for_selected_competetion = upload_submission_file
        self.download_competetion_dataset_for_selected_challenge = download_dataset
        self.print_user_daily_remaining_submission_competetion = daily_submission_remaining
        self.daily_submission_limit_data = None
        self.report_dataframe = report_dataframe
        self.user = user




    def selected_competitions_to_work(self,selected_competition_list: list):
        """Get name of selected competition to work with for submission process and others."""

        open_challenge_data = self.user.get_opened_challenges(reward="all", kind="competition",
                                                         fixed_index=None, open_competetion=True)
        logger.info(f"Opened_competitions {open_challenge_data['id'].tolist()}")

        for current_selected_challenge in selected_competition_list:
            self.user.select_a_challenge(reward="all", kind="competition", fixed_index=None, open_competetion=True,
                                    comptetion_name=current_selected_challenge)
            current_selected_challenge = self.user.which_challenge
            logger.info(f"Processing Competition : {current_selected_challenge}")

            daily_remaining_submission_data = self.user.availabel_remaining_submission_for_selected_competetion(
                current_selected_challenge)

            leader_board_data =self.user.get_leaderboard_data(user_name="MuhammadQasimShabbeer")

            if self.print_user_daily_remaining_submission_competetion:
                logger.info(f"before submission file posting remaining submission {daily_remaining_submission_data['data']['today']}")


            if self.print_leader_board_for_selected_competetion:
                self.user.leaderboard(current_selected_challenge, user_name_for_rank="MuhammadQasimShabeer")

            if self.print_user_rank_for_selected_competetion:
                rank = self.user.my_rank(current_selected_challenge, user_name_for_rank="MuhammadQasimShabeer")
                logger.info(f" your current rank in this competetion is {rank}")

            if self.download_competetion_dataset_for_selected_challenge:
                self.user.download_dataset(destination="output")  # Download the dataset of the selected challenge
                logger.info(f"data is download successfully for {current_selected_challenge}")
                # # user.submission_board()

            if self.submit_submission_file_for_selected_competetion:
                logger.info(f"Starting Submissions posting for {current_selected_challenge}")
                competition_directory = os.path.join(CONFIG.ZindiCompetetionFilesPath.competetion_folder,
                                                     current_selected_challenge)

                submission_files = [
                        os.path.join(str(competition_directory), f)
                        for f in os.listdir(str(competition_directory))
                        if f.endswith(".csv")
                    ]
                logger.info(f"Total submission files {len(submission_files)} for competetion in Submission In Progress")
                for submission_file in submission_files:
                    self.user.submit(filepaths=[submission_file], comments=['API  submission'])
                    rank_after_submission = self.user.my_rank(current_selected_challenge, user_name_for_rank="MuhammadQasimShabeer")
                    daily_limit_data_after_submission = self.user.availabel_remaining_submission_for_selected_competetion(
                            current_selected_challenge)

                    today_remaining = daily_limit_data_after_submission['data']['today']
                    today_submitted = daily_limit_data_after_submission['data']['submitted_today']

                    report_dataframe_new_row = {
                        "Competetion Name":current_selected_challenge,
                        "today_remaining_submission":today_remaining,
                        "today_total_submitted": today_submitted,
                        "Best Score": leader_board_data[1] ,
                        "Best rank": leader_board_data[0],
                        "user name" : leader_board_data[2],
                        "Best submission time" : leader_board_data[3],
                        "rank after submission": rank_after_submission,
                    }

                    self.report_dataframe.loc[len(self.report_dataframe)] = report_dataframe_new_row
            logger.info(f"Submission posting Completed {current_selected_challenge}")
        self.report_dataframe.to_csv(CONFIG.ReportsFiles.submission_posted_report, index=False)
        logger.info(f"========== Reported Generated Complete ================")

