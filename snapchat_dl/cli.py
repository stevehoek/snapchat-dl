#======================================================================================================================
# Command parser for Snapchat Downloader.
#======================================================================================================================

import argparse
import os
import sys

#----------------------------------------------------------------------------------------------------------------------
def parseArguments():
    """Command parser for Snapchat Downloader."""
#----------------------------------------------------------------------------------------------------------------------
    parser = argparse.ArgumentParser(prog="snapchat-dl")

    parser.add_argument(
        "username",
        action="store",
        nargs="*",
        help="One or more usernames to download content for.",
    )

    parser.add_argument(
        "-r",
        "--root-folder",
        action="store",
        default=os.path.abspath(os.getcwd()),
        help="Location to store downloaded content.",
        dest="rootFolder",
    )

    parser.add_argument(
        "-f",
        "--scan-root-folder",
        action="store_true",
        help="Scan usernames (as folder name) from root folder.",
        dest="scanRootFolder",
    )

    parser.add_argument(
        "-b",
        "--scan-batch-file",
        action="store",
        default=None,
        help="Read usernames from batch file (one username per line).",
        dest="batchFile",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c",
        "--scan-clipboard",
        action="store_true",
        help="Scan clipboard for story links"
        " ('https://story.snapchat.com/<s>/<username>').",
        dest="scanClipboard",
    )

    group.add_argument(
        "-u",
        "--check-for-update",
        action="store_true",
        help="Periodically check for new content.",
        dest="checkUpdate",
    )

    parser.add_argument(
        "-ss",
        "--skip-stories",
        action="store_true",
        help="Skip downloading public stories.",
        dest="skipStories",
    )

    parser.add_argument(
        "-sc",
        "--skip-curated",
        action="store_true",
        help="Skip downloading curated highlights.",
        dest="skipCurated",
    )

    parser.add_argument(
        "-sh",
        "--skip-spotlight",
        action="store_true",
        help="Skip downloading spotlight highlights.",
        dest="skipSpotlight",
    )

    parser.add_argument(
        "-d",
        "--dump-json",
        action="store_true",
        help="Save snap metadata to a JSON file next to downloaded content.",
        dest="dumpJSON",
    )

    parser.add_argument(
        "-g",
        "--generate-scripts",
        action="store_true",
        help="Generate shell scripts for combining multipart stories.",
        dest="generateScripts",
    )

    parser.add_argument(
        "-nm",
        "--no-multipart",
        action="store_true",
        help="Don't combine multipart stories.",
        dest="noMultipart",
    )
    
    parser.add_argument(
        "-w",
        "--max-workers",
        action="store",
        default=4,
        help="Set maximum number of parallel downloads. (Default: 4)  NOTE: only applies when --no-multipart arg is present",
        dest="maxWorkers",
        type=int,
    )

    parser.add_argument(
        "-ui",
        "--update-interval",
        action="store",
        default=60 * 10,
        help="Set the update interval for checking new content in seconds. (Default: 600s)",
        dest="updateInterval",
        type=int,
    )

    parser.add_argument(
        "-si",
        "--sleep-interval",
        action="store",
        default=1,
        help="Sleep between downloads in seconds. (Default: 1s)",
        dest="sleepInterval",
        type=int,
    )

    parser.add_argument(
        "-fast",
        "--fast",
        action="store_true",
        help="Skip online size checks for snap media.",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Do not print anything but errors to the console.",
    )

    parser.add_argument(
        "-a",
        "--automated",
        action="store_true",
        help="Change logging style when run under automation (eg: Shortcuts).",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()

#======================================================================================================================
#======================================================================================================================
