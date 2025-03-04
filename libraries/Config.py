from pathlib import Path
import os


class Configuration:
    logger_file_path = "app.log"

    class DIRECTORIES:
        """
        This class serves as a container for any directories you require for your automation
        these will be created automatically or would already exist
        """

        TEMP = Path().cwd() / "temp"
        OUTPUT = Path().cwd() / "output"
        REPORT = OUTPUT / "submission_report.csv'"
        SUBMSSION_FILES = Path().cwd() / f"{OUTPUT}/subimssionfiles"
        OUTPUT_SCREENSHOTS = os.path.join(OUTPUT, "screenshots")
        MAPPING = OUTPUT / "mapping"

    class ReportsFiles:
        """Reports of submissions of competitions."""
        reports_columns = ["Competetion Name", "today_remaining_submission", "today_total_submitted",
         "Best Score", "Best rank", "user name", "Best submission time", "Rank after submission"]


        submission_posted_report = "submission_report.csv"

    class CredentialsGroups:
        """List of Credential groups."""
        items_list = ["Phantom Wallet","Zindi_Credential"]

    class ZindiCompetetionFilesPath:
        """zindi competetions files paths."""
        competetion_folder = Path().cwd() / "Competitions"
        submission_file_folder = 'SubmissionFilesFolder'

    class INPUTS:
        selected_competetion_names_to_work = [
            "lacuna-solar-survey-challenge",
            "cgiar-root-volume-estimation-challenge",
            "lelapa-ai-buzuzu-mavi-challenge"
        ]
        download_dataset_for_selected_competetion_name = False
        show_leader_board = False
        user_rank_for_selected_competetion = True
        upload_submission_file = True
        show_daily_submission = True

CONFIG = Configuration()
