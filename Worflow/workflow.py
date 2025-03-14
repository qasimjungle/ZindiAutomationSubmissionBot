import pandas as pd
from libraries.bitwarden_credential import BitwardenCredentialManagement
from libraries.exception import FileSizeTooLargeToSendThroughGmail
from libraries.utils import Utils
from libraries.zindi.user import Zindian
from libraries.zindi_site import ZindiProcessing
from Worflow.process import  ProcessPreparation
from  libraries.logging_file import  logger
from libraries.Config import CONFIG

class Processes:
    """whole processes."""

    def __init__(self):
        self.bitwarden = BitwardenCredentialManagement()
        self.credential = self.bitwarden.get_bitwarden_credentials(CONFIG.CredentialsGroups.items_list)
        self.user = Zindian(username=self.credential['Zindi_Credential']['username'],
                       fixed_password=self.credential['Zindi_Credential']['password'])
        logger.info(" Logged into Zindi Successfully using api.")
        self.report_dataframe = pd.DataFrame()
        self.preparation_process = ProcessPreparation(zindi_user=self.user)
        self.report_columns = CONFIG.ReportsFiles.reports_columns
        self.show_leaderboard = CONFIG.INPUTS.show_leader_board
        self.show_rank = CONFIG.INPUTS.user_rank_for_selected_competetion
        self.upload_submission_file = CONFIG.INPUTS.upload_submission_file
        self.download_dataset = CONFIG.INPUTS.download_dataset_for_selected_competetion_name
        self.show_daily_submission_remaining = CONFIG.INPUTS.show_daily_submission
        self.zindi_processing = ZindiProcessing(self.user,
        credentials=self.credential, show_leaderboard=self.show_leaderboard, show_rank=self.show_rank,
        upload_submission_file=self.upload_submission_file, download_dataset=self.download_dataset,
        daily_submission_remaining=self.show_daily_submission_remaining, report_dataframe=pd.DataFrame(columns=self.report_columns)
            )
        self.utils = Utils(credential=self.credential)


    def preparation_files_for_processing(self):
        """preparation for files processing."""
        self.preparation_process.get_opened_competetion_names_list_make_dirs()
        if  self.preparation_process.submission_files_checking():
            logger.info(" files format checks are passed.")
        selected_competition_list = self.preparation_process.make_selected_competitions_names_correct()
        selected_competition_list = self.preparation_process.keep_selected_competitions_which_open_competition(selected_competition_list)
        selected_competition_list = self.preparation_process.keep_selected_competitions_submission_limit_not_reach(selected_competition_list)
        self.preparation_process.check_if_selected_competetion_list_not_empty(selected_competition_list)
        return selected_competition_list


    def process_zindi_site(self,submission_files_checking:list) -> None:
        """proceses zindi site."""
        self.zindi_processing.selected_competitions_to_work(submission_files_checking)

    # todo  this method implementation if i have time in future
    # def generation_of_report(self):
    #     """generation of Report of all Competetion Submission Process."""
    #     pass


    def sending_report_to_gmail(self):
        """send reprot to user email report."""
        try:
            files_size_dict = self.utils.check_size_of_attachement_sending_email(list(CONFIG.DIRECTORIES.REPORT))
            for file_name,file_size in files_size_dict.items():
               if file_size >= 25.0:
                   logger.info("File has 25MB or more only uploading to sharepoint")
                   raise FileSizeTooLargeToSendThroughGmail
               self.utils.sending_report_using_email(file_size)
               logger.info("============== Files Send to Gmail.=================")
        except Exception as e:
            logger.error(e)
        finally:
            # todo  try to upload file to Sharepoint either way if send to gmail or or not.
            pass



    def start(self):
        """start processing."""
        selected_competition_list = self.preparation_files_for_processing()
        self.process_zindi_site(selected_competition_list)
        self.sending_report_to_gmail()
