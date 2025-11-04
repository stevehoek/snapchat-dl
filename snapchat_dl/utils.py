#======================================================================================================================
# Utility functions for Snapchat Downloader.
#======================================================================================================================

import json
import os
import re

from argparse   import Namespace
from datetime   import datetime
from loguru     import logger       # pyright: ignore[reportMissingImports]

#----------------------------------------------------------------------------------------------------------------------
class UserNotFoundError(Exception):
    """User not found"""
#----------------------------------------------------------------------------------------------------------------------
    pass


#----------------------------------------------------------------------------------------------------------------------
def strftime(timestamp:int, format:str):
    """
    Format unix timestamp to custom format.

    Args:
        timestamp (int): unix timestamp
        format (str): valid python date time format

    Returns:
        str: timestamp formatted to custom format.
    """
#----------------------------------------------------------------------------------------------------------------------
    return datetime.utcfromtimestamp(timestamp).strftime(format)


#----------------------------------------------------------------------------------------------------------------------
def strftrunc(s, n):
#----------------------------------------------------------------------------------------------------------------------
    if len(s) <= n:
        # string is already short-enough
        return s
    # half of the size, minus the 3 .'s
    n_2 = int(n) / 2 - 3
    n_2 = int(n_2)
    # whatever's left
    n_1 = n - n_2 - 3
    return '{0}...{1}'.format(s[:n_1], s[-n_2:])


#----------------------------------------------------------------------------------------------------------------------
def validateUsername(username:str):
    """
    Validate Username.

    Args:
        username (str): Snapchat Username

    Returns:
        bool: True if username is valid.
    """
#----------------------------------------------------------------------------------------------------------------------
    match = re.match(r"(?P<username>^[\-\w\.\_]{3,15}$)", username)
    if match is None:
        return False

    return match and match.groupdict()["username"] == username


#----------------------------------------------------------------------------------------------------------------------
def searchUsernames(usernames: str) -> list:
    """
    Return list of usernames found in a string.

    Args:
        usernames (str): usernames to search 

    Returns:
        list: valid username matches found in usernames
    """
#----------------------------------------------------------------------------------------------------------------------
    return list(
        sorted(
            set(
                [
                    username
                    for username in re.findall(
                        r"https?://(?:story|www).snapchat.com/(?:[suad]+/|@)([\-\w\.\_]{3,15})",
                        usernames,
                    )
                    if validateUsername(username)
                ]
            )
        )
    )


#----------------------------------------------------------------------------------------------------------------------
def processBatchFile(args: Namespace) -> list:
    """
    Return list of usernames from file args.batchFile.

    Args:
        args (Namespace): argparse Namespace

    Returns:
        list: usernames read from batchFile
    """
#----------------------------------------------------------------------------------------------------------------------
    usernames = list()
    if args.batchFile is not None:
        if os.path.isfile(args.batchFile) is False:
            logger.opt(colors=True).error("[x] <red>Invalid batch file at <blue>{}</blue></red>\n".format(args.batchFile))
            return []

        with open(args.batchFile, "r") as file:
            for user in file.read().split("\n"):
                username = user.strip()
                if validateUsername(username) and username not in usernames:
                    usernames.append(username)

        logger.opt(colors=True).info("\nAdded {} usernames from <blue>{}</blue>\n".format(len(usernames), args.batchFile))

    return usernames


#----------------------------------------------------------------------------------------------------------------------
def processRootFolder(args: Namespace):
    """
    Return dirnames as username from file args.rootFolder.

    Args:
        args (Namespace): argparse Namespace

    Returns:
        list: usernames read from root folder
    """
#----------------------------------------------------------------------------------------------------------------------
    usernames = list()
    if args.scanRootFolder:
        if os.path.isdir(args.rootFolder) is False:
            logger.opt(colors=True).error("[x] <red>Root folder does not exist at <blue>{}</blue></red>\n".format(args.rootFolder))
            return []

        for folder in os.listdir(args.rootFolder):
            if os.path.isdir(os.path.join(args.rootFolder, folder)):
                if folder not in usernames and validateUsername(folder):
                    usernames.append(folder)
        
        logger.opt(colors=True).info("\nAdded {} usernames from <blue>{}</blue>\n".format(len(usernames), args.rootFolder))

    return list(sorted(set(usernames)))


#----------------------------------------------------------------------------------------------------------------------
def dumpTextFile(content: str, pathname: str):
    """
    Write content to pathname using `tx` mode.

    Args:
        content (str): File content to write.
        pathname (str): absolute path of file to be written.

    This will overwrite the file.
    """
#----------------------------------------------------------------------------------------------------------------------
    folder = os.path.dirname(pathname)

    os.makedirs(folder, exist_ok=True)

    if os.path.isfile(pathname):
        os.remove(pathname)

    with open(pathname, "w+") as file:
        file.write(content)


#----------------------------------------------------------------------------------------------------------------------
def dumpResponse(content: dict, pathname: str):
    """
    Save JSON file

    Args:
        content: JSON data
        pathname (str): absolute path of file to be written.

    Returns:
        None
    """
#----------------------------------------------------------------------------------------------------------------------
    dumpTextFile(json.dumps(content, indent=4), pathname)

#======================================================================================================================
#======================================================================================================================
