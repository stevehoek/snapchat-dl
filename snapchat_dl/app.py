#======================================================================================================================
# Commandline setup for Snapchat Downloader.
#======================================================================================================================

import sys
import time

import pyperclip                                            # pyright: ignore[reportMissingModuleSource]

from datetime                   import datetime
from datetime                   import timedelta
from dateutil                   import tz                   # pyright: ignore[reportMissingModuleSource]
from timeit                     import default_timer as timer

from loguru                     import logger               # pyright: ignore[reportMissingImports]

from snapchat_dl.snapchat_dl    import SnapchatDL           # pyright: ignore[reportMissingImports]
from snapchat_dl.cli            import parseArguments       # pyright: ignore[reportMissingImports]
from snapchat_dl.utils          import searchUsernames      # pyright: ignore[reportMissingImports]
from snapchat_dl.utils          import processRootFolder    # pyright: ignore[reportMissingImports]
from snapchat_dl.utils          import processBatchFile     # pyright: ignore[reportMissingImports]
from snapchat_dl.utils          import UserNotFoundError    # pyright: ignore[reportMissingImports]
from snapchat_dl.utils          import strftime             # pyright: ignore[reportMissingImports]

historyUsernames = list()

#----------------------------------------------------------------------------------------------------------------------
def _downloadUsers(downloader, usernames: list, respectHistory=False, sleepInterval=1):
    """
    Download public content from a list of usernames.

    Args:
        usernames (list): List of usernames to download.
        respectHistory (bool, optional): append username to history. Defaults to False.
    """
#----------------------------------------------------------------------------------------------------------------------
    for username in usernames:
        time.sleep(sleepInterval)

        if respectHistory is True:
            if username not in historyUsernames:
                historyUsernames.append(username)
                try:
                    downloader.DownloadSnaps(username)
                except UserNotFoundError:
                    return
        else:
            try:
                downloader.DownloadSnaps(username)
            except UserNotFoundError:
                return


#----------------------------------------------------------------------------------------------------------------------
def main():
    """
    Download a user's public content from Snapchat.
    """
#----------------------------------------------------------------------------------------------------------------------
    start = timer()

    args = parseArguments()

    env = "LOCALLY"
    logColor = True
    if args.automated is True:
        logColor=False
        env = "AUTOMATED"

    def logFilterScreen(record):
        if args.quiet is True:
            return (record["level"].name == "DEBUG") or (record["level"].name == "ERROR")    
        elif args.automated is True:
            return record["level"].name != "INFO"
        else:
            return True

    def logFilterFile(record):
        return (record["level"].name == "SUCCESS") or (record["level"].name == "ERROR") or (record["level"].name == "DEBUG")

    logger.remove()
    logger.add(sys.stderr, filter=logFilterScreen, colorize=logColor, format="<bold>{message}</bold>")
    logger.add("SnapchatDL.log", rotation="daily", colorize=False, format="{message}")
    if args.automated is True:
        logger.add("SnapchatDL-Automated.log", rotation="weekly", filter=logFilterFile, colorize=False, format="{message}")

    dtUTC = datetime.now(tz.tzutc())
    dtLocal = datetime.now(tz.tzlocal())
    dtHome = datetime.now(tz.gettz('America/Detroit'))
    offsetHome = dtHome.utcoffset() / timedelta(hours=1)
    dtLocal = dtUTC + timedelta(hours=offsetHome)
    timeStr = strftime(dtLocal.timestamp(), "%m-%d-%Y %H:%M")
    msg = "\n" + \
          "------------------------------------------------------------------------------------\n" + \
          "<yellow>SnapchatDL 3.0.0</yellow> (running <green>{}</green> at <cyan>{}</cyan>)\n".format(env, timeStr) + \
          "------------------------------------------------------------------------------------"
    if args.automated is True:
        logger.opt(colors=True).success(msg)
    else:
        logger.opt(colors=True).info(msg)

    if args.scanRootFolder or args.batchFile:
        usernames = processBatchFile(args) + processRootFolder(args)
        if not usernames:
            return
    else:
        usernames = args.username

    downloader = SnapchatDL(
        rootFolder=args.rootFolder,
        maxWorkers=args.maxWorkers,
        sleepInterval=args.sleepInterval,
        quiet=args.quiet,
        automated=args.automated,
        dumpJSON=args.dumpJSON,
        noMultipart=args.noMultipart,
        generateScripts=args.generateScripts,
        skipStories=args.skipStories,
        skipCurated=args.skipCurated,
        skipSpotlight=args.skipSpotlight,
        fast=args.fast,
    )

    try:
        _downloadUsers(downloader, usernames)

        if args.scanClipboard is True:
            logger.info("\nListening for valid Snapchat story links added to the clipboard")

            while True:
                clipboardUsernames = searchUsernames(pyperclip.paste())
                if len(clipboardUsernames) > 0:
                    _downloadUsers(downloader, clipboardUsernames, respectHistory=True)

                time.sleep(1)

        if args.checkUpdate is True:
            logger.info("\nScheduling updates for {} users".format(len(usernames)))

            while True:
                _downloadUsers(downloader, usernames)
                time.sleep(args.updateInterval)

        end = timer()
        elapsedSeconds = (end - start)
        elapsedMinutes = elapsedSeconds / 60
        elapsedTime = elapsedMinutes
        timeUnit = "minutes"
        if (elapsedMinutes < 1):
            elapsedTime = elapsedSeconds
            timeUnit = "seconds"

        msg = "\n" + \
            "------------------------------------------------------------------------------------\n" + \
            "<green>Completed in</green> <cyan>{}</cyan> <green>{}</green>\n".format(round(elapsedTime, 1), timeUnit) + \
            "------------------------------------------------------------------------------------\n"
        if args.automated is True:
            logger.opt(colors=True).success(msg)
        else:
            logger.opt(colors=True).info(msg)

    except KeyboardInterrupt:
        exit(0)

#----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())

#======================================================================================================================
#======================================================================================================================
