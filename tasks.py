from  Worflow.workflow import  Processes


def task():
    """Point of entry for oue Digital Workers process"""
    process = Processes()
    try:
        process.start()
    except Exception as e:
        raise e

if __name__ == "__main__":
        task()

