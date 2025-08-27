import dropbox
from dropbox.files import WriteMode
from typing import Optional
from services.settings import settings


def _client() -> dropbox.Dropbox:
    token = settings.DROPBOX_ACCESS_TOKEN
    if not token:
        raise RuntimeError("DROPBOX_ACCESS_TOKEN not set")
    dbx = dropbox.Dropbox(token, timeout=60)
    dbx.users_get_current_account()  # validate
    return dbx


def upload_markdown(project_id: str, doc_id: str, content_md: str) -> str:
    """
    Uploads parsed markdown to Dropbox at /parsed/{project_id}/{doc_id}.md
    and overwrites if it already exists. Returns the Dropbox path.
    """
    dbx = _client()
    path = f"/parsed/{project_id}/{doc_id}.md"
    # Important: filenames/paths must start with '/' per SDK expectations.
    dbx.files_upload(
        content_md.encode("utf-8"),
        path,
        mode=WriteMode.overwrite,  # correct enum usage
        mute=True,
        strict_conflict=False,
    )
    return path


def get_or_create_shared_link(path: str) -> str:
    """
    Returns a shareable link for the file. If none exists, creates one.
    Converts ?dl=0 to ?dl=1 for direct download.
    """
    dbx = _client()
    result = dbx.sharing_list_shared_links(path=path, direct_only=True)
    url: Optional[str] = None
    if result and getattr(result, "links", None):
        if len(result.links) > 0 and getattr(result.links, "url", None):
            url = result.links.url
    if not url:
        link_md = dbx.sharing_create_shared_link_with_settings(path)
        url = link_md.url
    if url and url.endswith("?dl=0"):
        url = url[:-1] + "1"
    if not url:
        raise RuntimeError(f"Could not obtain a shared link for path: {path}")
    return url


def upload_and_share_markdown(project_id: str, doc_id: str, content_md: str) -> str:
    """
    High-level helper: upload the .md then return a direct-download shared link.
    """
    path = upload_markdown(project_id, doc_id, content_md)
    return get_or_create_shared_link(path)
