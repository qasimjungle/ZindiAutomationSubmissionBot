import smtplib
import mimetypes
import os
from email.message import EmailMessage
import shutil
from libraries.Config import CONFIG



class Utils:
    """utils method defined"""
    def __init__(self,credential):
        self.credential = credential


    def check_size_of_attachement_sending_email(self, file_paths: list) -> dict:
            """check size of email before sending."""
            file_sizes = {}
            for file_path in file_paths:
                try:
                    # Get the file size in bytes
                    file_size_bytes = os.path.getsize(file_path)
                    # Convert the size to MB
                    file_size_mb = file_size_bytes / (1024 * 1024)
                    file_sizes[file_path] = round(file_size_mb, 2)  # Round to 2 decimal places
                    print(f"File: {file_path}, Size: {file_sizes[file_path]} MB")
                except FileNotFoundError:
                    print(f"File {file_path} not found.")
                    file_sizes[file_path] = None
            return file_sizes

    def sending_report_using_email(self,REPORT_PATH):
            """Sending generated report to given emails."""
            # Email Configuration
            SMTP_SERVER = "smtp.gmail.com"
            SMTP_PORT = 587
            EMAIL_SENDER = ####  User Here sender  emails 
            AppPassword = # Use the generated App Password for gmail account to send gmails 
            EMAIL_RECEIVER = ######### address of emails reveirer 
            SUBJECT = "Automated Report"
            BODY = "Hello,\n\nPlease find the attached report.\n\nBest Regards, Asad Khan"

            # Create Email
            msg = EmailMessage()
            msg["From"] = EMAIL_SENDER
            msg["To"] = EMAIL_RECEIVER
            msg["Subject"] = SUBJECT
            msg.set_content(BODY)

            # Attach File
            if os.path.exists(REPORT_PATH):
                with open(REPORT_PATH, "rb") as file:
                    file_data = file.read()
                    file_type, _ = mimetypes.guess_type(REPORT_PATH)
                    file_type = file_type or "application/octet-stream"
                    msg.add_attachment(
                        file_data,
                        maintype=file_type.split("/")[0],
                        subtype=file_type.split("/")[1],
                        filename=os.path.basename(REPORT_PATH),
                    )

            # Send Email
            try:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_SENDER, AppPassword)
                    server.send_message(msg)
                print("✅ Email sent successfully to", EMAIL_RECEIVER)
            except Exception as e:
                print(f"❌ Error sending email: {e}")


    def sending_reports_using_email(self,reports_files_path):
        """files paths to send as report to given user"""
        files_size_dict =  self.check_size_of_attachement_sending_email(reports_files_path)
        for REPORT_PATH in reports_files_path:
            self.sending_report_using_email(REPORT_PATH)


def remove_subdirectories(parent_dir):
    """Remove all directories inside the given parent directory."""
    if not os.path.exists(parent_dir):
        print(f"Path does not exist: {parent_dir}")
        return

    for item in os.listdir(parent_dir):
        item_path = os.path.join(parent_dir, item)
        if os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
                print(f"Removed directory: {item_path}")
            except Exception as e:
                print(f"Failed to remove {item_path}: {e}")


    logger.info("remove sub directory from competition folder")
