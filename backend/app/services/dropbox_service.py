# utils/dropbox_client.py
import os
from typing import Optional, Tuple
import dropbox
from dropbox.files import WriteMode, UploadSessionCursor, CommitInfo


class DropboxClient:
    def __init__(self, access_token: str):
        """
        Initialize Dropbox client with a user access token.
        """
        self.dbx = dropbox.Dropbox(access_token)

    def upload_file(self, local_path: str, dropbox_path: str, overwrite: bool = True):
        """
        Upload a small file (<150MB) to Dropbox.
        """
        mode = WriteMode.overwrite if overwrite else WriteMode.add
        with open(local_path, "rb") as f:
            data = f.read()
        res = self.dbx.files_upload(data, dropbox_path, mode=mode)

    def download_file(
        self, dropbox_path: str, local_dest: Optional[str] = None
    ) -> Tuple[dict, bytes]:
        """
        Download a file from Dropbox; optionally write to local path.
        """
        md, resp = self.dbx.files_download(path=dropbox_path)
        data = resp.content
        if local_dest:
            with open(local_dest, "wb") as f:
                f.write(data)
        return (md.__dict__, data)

    def delete_file(self, dropbox_path: str) -> dict:
        """
        Delete a file from Dropbox.
        """
        res = self.dbx.files_delete_v2(path=dropbox_path)
        return res.__dict__


dropbox_client = DropboxClient(
    "sl.u.AF-WXRlXmyso-N9fThbJmio-xV6iULs5VTacYzyS55as5cl745-faUqhGxqmICHBMOpyE7pTKXua6Z75r87tH_ISzsOKupxYXbxzvsGjpM5NQr2Y4g5S2z18AYa4WKpRG-qJu8EG6MoMQxAmw1Y-dK11RA3SpJKqRjU16M1rOwffq-ebMs5jVkd2mGgyOGlqIkdKu4kGBB1HvrWTKs5vd5935waRa6OU3E3clvN0OuUC-IC1asaGbf_QqlatHkSyW0pea2RqvmLGRq6T9GsWFeGrrBLjjiL2FlAJ1I9ji4Ec_DsS0fi8Wp9Me9zEdr2Abc14JfJhImRebQBAOhxkC3IdK7fiN0ydYASiRZGgfkNEgGs28pKBDUBF3syUEyQEATSRhC19OKFXp3FWH0Npydh_bsNOvlBAG5zKgKo1VOf-8OlK3radNuwVoWsxrCO_llZ3htgm1djOQIx676iTBLH-d34K1RIfyENGDAsX9gtvWcKIAGdx_J371P-B6tajFneI-ZgbUVL0UdzoXLt3FUzxE5tLQrQFlKxT4ZL63T3sbOYMSem4Zg9Row5gG08Dd-GX4f30Tc6xeMDtYvn6bV_-GvhobbdAr1ujiIQj6NsaCzDRo0iv6mMz-JhKdBBqDsXo0XOUHCmi5O4-IU29VQAUSMUoCuKlEGTDMZQ8S6DlxBKHj_uX5XINbFXlVfXZICJn5V2QPcJQW0KpfnNjYuYKVzI-UWkMzfXDayl99qHRf5YdvdHVm_NUhn_BmU1LeGC67v6AhxJpQEyiGGSy6qMlgGrcN1LOOGI1ZxwmBHTaJSgdclDFfGeMnMuPptxJC4f0sjeV69a_2J_FtqP9KMrNzHK4rLr-DRefKZHjquEmxsQmUMfCVbfDusgxB_CQxD7NVx_Cjnoxzq15Da63hIStfpBsfbrS4RHdkbSlVli3uJtXV_jKmuIBdTLgHkPckFgdcrmuqrYea-s2uICLKEpK1C6qje6gtd7LonF7gz-e-zkFwRB0MW9zGXyMwFJ598dMA_XeBWbc8S5d4JLpoigH8ra24osb1yqB0AOSqWhCFBRwHT85g1henHd6qPdtMlOWKMmwO8vBKoR5Jt_FBhv8IK1nbo9391PtXEPvDkbZhRPmL3j_6lbKOG4gLMq4YMYm-4eJisrdeuBVG7dSxWSJ6KfuQsUBXCQbcWeTPyA9oDVjdev6P6xEYBixgHue0M5-ROPZm8V2SFWdgB8DYsQ_BAT_ZYgHjkj6tI-B3YEqDy0rf_DgMf-wKuavHxWGpJ7aa0BlyzlHhoeCRnsVdAcC"
)
