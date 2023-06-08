import subprocess

command = "nohup /usr/local/bin/cloud_sql_proxy -instances=review-tool-388312:us-central1:blackwidow=tcp:5432"
subprocess.Popen(command, shell=True)
