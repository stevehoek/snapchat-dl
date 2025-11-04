#======================================================================================================================
# File Downloader for Snapchat Downloader.
#======================================================================================================================

import os
import time
import requests                                 # pyright: ignore[reportMissingModuleSource]

from loguru                 import logger       # pyright: ignore[reportMissingImports]

from snapchat_dl.utils      import strftrunc    # pyright: ignore[reportMissingImports]

#----------------------------------------------------------------------------------------------------------------------
def DownloadUrl(url:str, pathname:str, sleepInterval:int=0, quiet:bool=False, automated:bool=False, skipSizeCheck:bool=False):
    """
    Download URL to destionation pathname.

    Args:
        url (str): url to download
        pathname (str): absolute path to destination file
        sleepInterval (int): duration of sleep for rate limiting
        quiet (bool): only output errors
        skipSizeCheck (bool): don't validate the size with the HTTP headers

    Returns:
        bool: true if something is downloaded, false if not (due to error or skip)
    """
#----------------------------------------------------------------------------------------------------------------------
    filename = os.path.basename(pathname)

    #logger.opt(colors=True).debug("<blue>{}</blue>".format(url))

    if (os.path.isfile(pathname)):
        if skipSizeCheck:
            msg = "Skipping existing snap {}".format(filename)
            msg = strftrunc(msg, 70)
            msg = "\t<black>"+msg+"</black>"
            logger.opt(colors=True).info(msg)
            return False

    if len(os.path.dirname(pathname)) > 0:
        os.makedirs(os.path.dirname(pathname), exist_ok=True)

    try:
        response = requests.get(url, stream=True, timeout=10)
    except requests.exceptions.ConnectTimeout:
        response = requests.get(url, stream=True, timeout=10)

    try:
        if response.status_code != requests.codes.ok:   #requests.codes.get("ok")
            raise response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.opt(colors=True).error("<red>HTTPError {}</red> for <blue>{}</blue>", requests.Response().status_code, url)
        return False

    try:
        skipDownload = False
        if (os.path.isfile(pathname)):
            if "content-length" in response.headers:
                if (not skipSizeCheck and os.path.getsize(pathname) == int(response.headers.get("content-length"))):
                    skipDownload = True
        
        if not skipDownload:
            logger.opt(colors=True).info("\tDownloading new snap <blue>{}</blue>".format(filename))
        
            if (os.path.isfile(pathname)):
                os.remove(pathname)

            with open(pathname, "xb") as handle:
                try:
                    for data in response.iter_content(chunk_size=4194304):
                        handle.write(data)
                    handle.close()
                except requests.exceptions.RequestException as e:
                    logger.opt(colors=True).error("<red>"+e.strerror+"/red")

            #Rate limiting
            time.sleep(sleepInterval)

            return True
        else:
            raise FileExistsError
            
    except FileExistsError:
        msg = "Skipping existing snap {}".format(filename)
        msg = strftrunc(msg, 70)
        msg = "\t<black>"+msg+"</black>"
        logger.opt(colors=True).info(msg)
        return False

#======================================================================================================================
#======================================================================================================================
