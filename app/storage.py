import os, json, time
from typing import List, Optional

class Storage:
    def __init__(self):
        self.base = os.getenv("JOBS_DIR", "./jobs")
        os.makedirs(self.base, exist_ok=True)

    def job_dir(self, job_id):
        d = os.path.join(self.base, job_id)
        os.makedirs(d, exist_ok=True)
        return d

    def init_job(self, job_id):
        d = self.job_dir(job_id)
        open(os.path.join(d,"status.log"), "a").close()

    def append_status(self, job_id, message: str):
        d = self.job_dir(job_id)
        with open(os.path.join(d, "status.log"), "a", encoding="utf-8") as f:
            f.write(message + "\n")

    def read_status(self, job_id) -> list:
        d = self.job_dir(job_id)
        fpath = os.path.join(d, "status.log")
        if not os.path.exists(fpath):
            return []
        with open(fpath, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
        return lines

    def save_json(self, job_id, name, obj):
        d = self.job_dir(job_id)
        fpath = os.path.join(d, name)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)

    def save_artifact(self, job_id, name, local_path):
        return os.path.join(self.job_dir(job_id), name)

    def get_artifact_path(self, job_id, name):
        fpath = os.path.join(self.job_dir(job_id), name)
        return fpath if os.path.exists(fpath) else None
