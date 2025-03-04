class SelectedCompetitionListEmptyAfterProcessingError(Exception):
    """selected competition list is empty after preprocessing."""
    pass


class SubmissionFilesNotPresentFolder(Exception):
    """submission files missing from Folders."""
    pass


class  IncorrectSubmissionFilesNames(Exception):
    """files names Should be {competition_name_from_url}_{extra_name_submission_file}.csv"""
    pass

class FileSizeTooLargeToSendThroughGmail(Exception):
    """If file size exceed allowed limit of 25 MB in gmail."""