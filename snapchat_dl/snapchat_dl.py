#======================================================================================================================
# Base class for Snapchat Downloader.
#======================================================================================================================

import os
import re
import json
import subprocess
import shlex
import concurrent.futures
import requests                                             # pyright: ignore[reportMissingModuleSource]
import time

from datetime               import datetime
from datetime               import timedelta
from dateutil               import tz                       # pyright: ignore[reportMissingModuleSource]

from loguru                 import logger                   # pyright: ignore[reportMissingImports]

from pathlib                import Path

from snapchat_dl.downloader import DownloadUrl              # pyright: ignore[reportMissingImports]
from snapchat_dl.utils      import dumpResponse             # pyright: ignore[reportMissingImports]
from snapchat_dl.utils      import strftime                 # pyright: ignore[reportMissingImports]
from snapchat_dl.utils      import strftrunc                # pyright: ignore[reportMissingImports]
from snapchat_dl.utils      import UserNotFoundError        # pyright: ignore[reportMissingImports]

MEDIATYPES      = ["jpg", "mp4"]
MAXRETRYCOUNT   = 5

#----------------------------------------------------------------------------------------------------------------------
class SnapchatDL:
    """Download a user's public content from Snapchat."""
#----------------------------------------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------------------------------------
    def __init__(
        self,
        rootFolder=".",
        maxWorkers=4,
        sleepInterval=1,
        quiet=False,
        automated=False,
        dumpJSON=False,
        noMultipart=False,
        generateScripts=False,
        skipStories=False,
        skipCurated=False,
        skipSpotlight=False,
        fast=False
    ):
    #----------------------------------------------------------------------------------------------------------------------
        self.rootFolder = os.path.abspath(os.path.normpath(rootFolder))
        self.maxWorkers = maxWorkers
        self.sleepInterval = sleepInterval
        self.quiet = quiet
        self.automated = automated
        self.dumpJSON = dumpJSON
        self.noMultipart = noMultipart
        self.generateScripts = generateScripts
        self.skipStories = skipStories
        self.skipCurated = skipCurated
        self.skipSpotlight = skipSpotlight
        self.fast = fast

        self.apiEndpoint = "https://www.snapchat.com/add/{}/"
        self.apiRegEx = (
            r'<script\s*id="__NEXT_DATA__"\s*type="application\/json">([^<]+)<\/script>'
        )

        
    #----------------------------------------------------------------------------------------------------------------------
    def _apiRequestResponse(self, username:str):
        """
        Download public data for a given Snapchat user.

        Args:
            username (str): Snapchat `username`

        Returns:
            (str): response
        """
    #----------------------------------------------------------------------------------------------------------------------
        url = self.apiEndpoint.format(username)
        return requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            },
        ).text


    #----------------------------------------------------------------------------------------------------------------------
    def _parseUserProfile(self, content:dict, username:str):
    #----------------------------------------------------------------------------------------------------------------------
        if "userProfile" in content["props"]["pageProps"]:
            userProfile = content["props"]["pageProps"]["userProfile"]
            id = userProfile["$case"]
            return userProfile[id]
        else:
            raise UserNotFoundError


    #----------------------------------------------------------------------------------------------------------------------
    def _parsePublicStories(self, content: dict):
    #----------------------------------------------------------------------------------------------------------------------
        publicStories = content["props"]["pageProps"].get("story")
        if isinstance(publicStories, dict) and "snapList" in publicStories:
            return publicStories["snapList"]
        return []


    #----------------------------------------------------------------------------------------------------------------------
    def _parseCuratedHighlights(self, content: dict):
    #----------------------------------------------------------------------------------------------------------------------
        if "curatedHighlights" in content["props"]["pageProps"]:
            curatedHighlights = content["props"]["pageProps"]["curatedHighlights"]
            return curatedHighlights
        return []


    #----------------------------------------------------------------------------------------------------------------------
    def _parseSpotlightHighlights(self, content: dict):
    #----------------------------------------------------------------------------------------------------------------------
        if "spotlightHighlights" in content["props"]["pageProps"]:
            spotlightHighlights = content["props"]["pageProps"]["spotlightHighlights"]
            return spotlightHighlights
        return []


    #----------------------------------------------------------------------------------------------------------------------
    def _apiProcessResponse(self, username:str):
        """
        Process public data for a given Snapchat user.

        Args:
            username (str): Snapchat `username`

        Returns:
            (dict, dict, dict, dict, dict): content, userProfile, publicStories, curatedHighlights, spotlightHighlights
        """
    #----------------------------------------------------------------------------------------------------------------------
        try:
            response = self._apiRequestResponse(username)
            if not response:
                logger.opt(colors=True).error("<red>Empty response when calling Snapchat API for user <magenta>{}</magenta> [Code: {}]</red>", username, requests.Response().status_code)
                return [None, None, None, None, None]

            userFolder = os.path.join(self.rootFolder, username)
            dumpResponse(response, os.path.join(userFolder, username+"_response.json"))

            responseRawJSON = re.findall(self.apiRegEx, response)
            if not responseRawJSON:
                #logger.debug(response)
                logger.opt(colors=True).error("<red>Unable to parse raw response from Snapchat API for user <magenta>{}</magenta> [Code: {}]</red>", username, requests.Response().status_code)
                return [None, None, None, None, None]

            dumpResponse(responseRawJSON, os.path.join(userFolder, username+"_raw.json"))

            if responseRawJSON[0]:
                content = json.loads(responseRawJSON[0])
            else:
                #logger.debug(responseRawJSON)
                logger.opt(colors=True).error("<red>Unable to index parsed response from Snapchat API for user <magenta>{}</magenta> [Code: {}]</red>", username, requests.Response().status_code)
                return [None, None, None, None, None]

            userProfile = self._parseUserProfile(content, username)
            publicStories = self._parsePublicStories(content)
            curatedHighlights = self._parseCuratedHighlights(content)
            spotlightHighlights = self._parseSpotlightHighlights(content)

            return content, userProfile, publicStories, curatedHighlights, spotlightHighlights

        except requests.exceptions.ConnectTimeout:
            logger.opt(colors=True).error("<red>Connection timeout calling Snapchat API for user <magenta>{}</magenta> [Code: {}]</red>", username, requests.Response().status_code)
            return [None, None, None, None, None]

        except UserNotFoundError:
            logger.opt(colors=True).error("<red>[x] <magenta>{}</magenta> is not a valid user [Code: {}]</red>\n".format(username, requests.Response().status_code))
            return [None, None, None, None, None]

        except (IndexError, KeyError, ValueError):
            logger.opt(colors=True).error("<red>Exception calling Snapchat API for user <magenta>{}</magenta> [Code: {}]</red>", username, requests.Response().status_code)
            return [None, None, None, None, None]


    #----------------------------------------------------------------------------------------------------------------------
    def _findDisplayName(self, userProfile:dict):
        """
        Find the user's displayname from their profile.

        Args:
            userProfile (dict): Snapchat userProfile

        Returns:
            (str) displayname
        """
    #----------------------------------------------------------------------------------------------------------------------
        username = userProfile["username"]
        displayname = ""
        if "displayName" in userProfile:
            displayname = userProfile["displayName"]
        elif "title" in userProfile:
            displayname = userProfile["title"]

        return displayname


    #----------------------------------------------------------------------------------------------------------------------
    def _mergeMulti(self, folder:str, username:str, timestamp:int, filelist:str, count:int):
        """
        Combine multipart story segments.

        Args:
            self (object): this
            username (str): Snapchat `username`
            timestamp (int): Snapchat story 'timestamp'
            filelist (string): story segments (ffmpeg style)
            count (int): number of story segments

        Returns:
            (none)
        """
    #----------------------------------------------------------------------------------------------------------------------
        if count > 1:
            multipartFilename = strftime(timestamp, "%Y-%m-%d_%H-%M-%S_{}.mp4").format(username)
            multipartPathname = os.path.join(folder, multipartFilename)

            command = "/opt/homebrew/bin/ffmpeg"
            command += filelist
            command += " -y -loglevel quiet -filter_complex \"concat=n={}\" ".format(count)
#            command += " -y -loglevel quiet -filter_complex \"concat=n={}:v=1:a=1[outv][outa]\"".format(count)
#            command += " -map \"[outv]\""
#            command += " -map \"[outa]\" "
            command += "\""
            command += multipartPathname
            command += "\""

            if not os.path.isfile(multipartPathname):
                logger.opt(colors=True).info("\tCombining multipart story:\n\t\t<blue>{}</blue>".format(command))

                execCommand = shlex.split(command)
                subprocess.run(execCommand)
            else:
                msg = "Skipping existing multipart story {}".format(multipartFilename)
                msg = strftrunc(msg, 70)
                msg = "\t<black>"+msg+"</black>"
                logger.opt(colors=True).info(msg)

            if self.generateScripts: 
                self._genScript(multipartPathname, command)


    #----------------------------------------------------------------------------------------------------------------------
    def _genScript(self, pathname:str, command:str):
        """
        Generates an executable shell script to perform a multipart story merge

        Args:
            pathname (str): pathname of file to generate
            command (str): command to write

        Returns:
            (none)
        """
    #----------------------------------------------------------------------------------------------------------------------
        folder = os.path.dirname(pathname)
        filename = Path(pathname).stem + ".sh"
        pathname = os.path.join(folder, filename)

        if os.path.isfile(pathname):
            os.remove(pathname)

        logger.opt(colors=True).info("\tGenerating script <blue>{}</blue>".format(filename))

        with open(pathname, "w+") as file:
            file.write("#! /usr/bin/env bash")
            file.write("\n")
            file.write("\n")
            file.write(command)
            file.write("\n")

        exec = shlex.split("chmod +x " + pathname)
        subprocess.run(exec)


    #----------------------------------------------------------------------------------------------------------------------
    def _downloadPublicStories(self, userProfile:dict, publicStories:dict):
        """
        Download Snapchat stories.

        Args:
            self (object): this
            userProfile (dict): Snapchat userProfile
            publicStories (dict): Snapchat stories

        Returns:
            (none)
        """
    #----------------------------------------------------------------------------------------------------------------------
        username = userProfile["username"]

        logger.opt(colors=True).info("\n[+] <magenta>{}</magenta> has {} public stories".format(username, len(publicStories)))

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.maxWorkers)
        try:
            lastTimestamp = 0
            multipartStoryCount = 1
            multipartFileList = ""
            downloadCount = 0

            for story in publicStories:
                id = story["snapId"]["value"]
                mediaURL = story["snapUrls"]["mediaUrl"]
                if len(mediaURL) == 0:
                    continue
                mediaType = story["snapMediaType"]
                timestampUTC = int(story["timestampInSec"]["value"])

                dtUTC = datetime.fromtimestamp(timestampUTC, tz.tzutc())
                tzLocal = tz.tzlocal()
                tzHome = tz.gettz('America/Detroit')
                dtLocal = datetime.now(tzLocal)
                dtHome = datetime.now(tzHome)
                offsetLocal = dtLocal.utcoffset() / timedelta(hours=1)
                offsetHome = dtHome.utcoffset() / timedelta(hours=1)
                dtLocal = dtUTC + timedelta(hours=offsetLocal)
                dtLocal = dtUTC + timedelta(hours=offsetHome)
                if dtLocal.dst() == timedelta(0):
                    dtLocal = dtLocal + timedelta(hours=1)
                timestampHome = dtHome.timestamp()
                timestampLocal = dtLocal.timestamp()
                dateFolder = strftime(timestampLocal, "%Y-%m-%d")

                dirname = os.path.join(self.rootFolder, username, "Public Stories", dateFolder)
                os.makedirs(dirname, exist_ok=True)

                if timestampLocal == lastTimestamp:
                    multipartStoryCount += 1
                else:
                    if not self.noMultipart:
                        multipartDateFolder = strftime(lastTimestamp, "%Y-%m-%d")
                        multipartFolder = os.path.join(self.rootFolder, username, "Public Stories", multipartDateFolder)
                        self._mergeMulti(multipartFolder, username, lastTimestamp, multipartFileList, multipartStoryCount)

                    multipartStoryCount = 1
                    multipartFileList = ""

                if mediaType == 0:
                    filename = strftime(timestampLocal, "%Y-%m-%d_%H-%M-%S_{}.{}").format(
                        username, MEDIATYPES[mediaType]
                    )
                else:
                    filename = strftime(timestampLocal, "%Y-%m-%d_%H-%M-%S_{}_part-{}.{}").format(
                        username, multipartStoryCount, MEDIATYPES[mediaType]
                    )
                    
                lastTimestamp = timestampLocal
                multipartFileList += " -i "
                multipartFileList += "\"" 
                multipartFileList += os.path.join(dirname, filename)
                multipartFileList += "\"" 

                if self.dumpJSON:
                    filename = os.path.join(dirname, Path(filename).stem + ".json")
                    mediaJSON = dict(story)
                    mediaJSON["snapUser"] = userProfile
                    logger.opt(colors=True).info("\tDumping story JSON:\n\t\t<blue>{}</blue>".format(os.path.basename(filename)))
                    dumpResponse(mediaJSON, filename)

                pathname = os.path.join(dirname, filename)
                if self.noMultipart:
                    executor.submit(DownloadUrl, mediaURL, pathname, self.sleepInterval, self.quiet, self.automated, self.fast)
                else:
                    if DownloadUrl(mediaURL, pathname, self.sleepInterval, self.quiet, self.automated, self.fast):
                        downloadCount += 1

            if not self.noMultipart:
                multipartDateFolder = strftime(lastTimestamp, "%Y-%m-%d")
                multipartFolder = os.path.join(self.rootFolder, username, "Public Stories", multipartDateFolder)
                self._mergeMulti(multipartFolder, username, lastTimestamp, multipartFileList, multipartStoryCount)

        except KeyboardInterrupt:
            executor.shutdown(wait=False)

        snapCount = len(publicStories)
        msg = "{} public stories downloaded ({}) or existing ({}) for <magenta>{}</magenta>".format(snapCount, downloadCount, snapCount-downloadCount, username)
        if (downloadCount > 0):
            msg = "[✔] " + msg
        else:
            msg = "[-] " + msg
        if (downloadCount > 0):
            logger.opt(colors=True).success(msg)
        elif not self.automated:
            logger.opt(colors=True).info(msg)


    #----------------------------------------------------------------------------------------------------------------------
    def _downloadCuratedHighlights(self, userProfile:dict, curatedHighlights:dict):
        """
        Download Snapchat curated highlights.

        Args:
            self (object): this
            userProfile (dict): Snapchat userProfile
            curatedHighlights (dict): Snapchat curated highlights

        Returns:
            (none)
        """
    #----------------------------------------------------------------------------------------------------------------------
        username = userProfile["username"]
        
        logger.opt(colors=True).info("\n[+] <magenta>{}</magenta> has {} curated highlights".format(username, len(curatedHighlights)))

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.maxWorkers)
        try:
             total = 0
             group = 0
             downloadCount = 0
             for highlight in curatedHighlights:
                #logger.debug(json.dumps(highlight, indent=4))
                groupTitle = highlight["storyTitle"]["value"]
                if len(groupTitle) == 0:
                    group += 1
                    groupTitle = "Highlight-{}".format(group)
                snapCount = 0
                snaps = highlight["snapList"]
                for snap in snaps:
                    #logger.debug(json.dumps(snap, indent=4))
                    #id = snap["snapId"]["value"]
                    mediaURL = snap["snapUrls"]["mediaUrl"]
                    if len(mediaURL) == 0:
                        continue
                    mediaType = snap["snapMediaType"]
                    timestampUTC = int(snap["timestampInSec"]["value"])

                    dtUTC = datetime.fromtimestamp(timestampUTC, tz.tzutc())
                    tzLocal = tz.tzlocal()
                    tzHome = tz.gettz('America/Detroit')
                    dtLocal = datetime.now(tzLocal)
                    dtHome = datetime.now(tzHome)
                    offsetLocal = dtLocal.utcoffset() / timedelta(hours=1)
                    offsetHome = dtHome.utcoffset() / timedelta(hours=1)
                    dtLocal = dtUTC + timedelta(hours=offsetLocal)
                    dtLocal = dtUTC + timedelta(hours=offsetHome)
                    if dtLocal.dst() == timedelta(0):
                        dtLocal = dtLocal + timedelta(hours=1)
                    timestampHome = dtHome.timestamp()
                    timestampLocal = dtLocal.timestamp()
                    dateFolder = strftime(timestampLocal, "%Y-%m-%d")

                    dirname = os.path.join(self.rootFolder, username, "Curated Highlights", groupTitle)
                    os.makedirs(dirname, exist_ok=True)

                    snapCount += 1
                    filename = strftime(timestampLocal, "%Y-%m-%d_%H-%M-%S_{}_curated_snap-{}.{}").format(
                        username, snapCount, MEDIATYPES[mediaType]
                    )

                    if self.dumpJSON:
                        filename = os.path.join(dirname, Path(filename).stem + ".json")
                        mediaJSON = dict(snap)
                        mediaJSON["snapUser"] = userProfile
                        logger.opt(colors=True).info("\tDumping curated highlight JSON:\n\t\t<blue>{}</blue>".format(os.path.basename(filename)))
                        dumpResponse(mediaJSON, filename)

                    pathname = os.path.join(dirname, filename)
                    if self.noMultipart:
                        executor.submit(DownloadUrl, mediaURL, pathname, self.sleepInterval, self.quiet, self.automated, self.fast)
                    else:
                        if DownloadUrl(mediaURL, pathname, self.sleepInterval, self.quiet, self.automated, self.fast):
                            downloadCount += 1
                    total += 1

        except KeyboardInterrupt:
            executor.shutdown(wait=False)

        snapCount = len(curatedHighlights)
        msg = "{} curated highlights containing {} snaps downloaded ({}) or existing ({}) for <magenta>{}</magenta>".format(snapCount, total, downloadCount, total-downloadCount, username)
        if (downloadCount > 0):
            msg = "[✔] " + msg
        else:
            msg = "[-] " + msg
        if (downloadCount > 0):
            logger.opt(colors=True).success(msg)
        elif not self.automated:
            logger.opt(colors=True).info(msg)


    #----------------------------------------------------------------------------------------------------------------------
    def _downloadSpotlightHighlights(self, userProfile:dict, spotlightHighlights:dict):
        """
        Download Snapchat spotlight highlights.

        Args:
            self (object): this
            userProfile (dict): Snapchat userProfile
            spotHighlights (dict): Snapchat spotlight highlights

        Returns:
            (none)
        """
    #----------------------------------------------------------------------------------------------------------------------
        username = userProfile["username"]
        
        logger.opt(colors=True).info("\n[+] <magenta>{}</magenta> has {} spotlight highlights".format(username, len(spotlightHighlights)))

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.maxWorkers)
        try:
             group = 0
             downloadCount = 0
             for highlight in spotlightHighlights:
                #logger.debug(json.dumps(highlight, indent=4))
                group += 1
                snapCount = 0
                snaps = highlight["snapList"]
                for snap in snaps:
                    #logger.debug(json.dumps(snap, indent=4))
                    #id = snap["snapId"]["value"]
                    mediaURL = snap["snapUrls"]["mediaUrl"]
                    if len(mediaURL) == 0:
                        continue
                    mediaType = snap["snapMediaType"]
                    timestampUTC = int(snap["timestampInSec"]["value"])

                    dtUTC = datetime.fromtimestamp(timestampUTC, tz.tzutc())
                    tzLocal = tz.tzlocal()
                    tzHome = tz.gettz('America/Detroit')
                    dtLocal = datetime.now(tzLocal)
                    dtHome = datetime.now(tzHome)
                    offsetLocal = dtLocal.utcoffset() / timedelta(hours=1)
                    offsetHome = dtHome.utcoffset() / timedelta(hours=1)
                    dtLocal = dtUTC + timedelta(hours=offsetLocal)
                    dtLocal = dtUTC + timedelta(hours=offsetHome)
                    if dtLocal.dst() == timedelta(0):
                        dtLocal = dtLocal + timedelta(hours=1)
                    timestampHome = dtHome.timestamp()
                    timestampLocal = dtLocal.timestamp()
                    dateFolder = strftime(timestampLocal, "%Y-%m-%d")

                    dirname = os.path.join(self.rootFolder, username, "Spotlight Highlights", dateFolder)
                    os.makedirs(dirname, exist_ok=True)

                    snapCount += 1
                    filename = strftime(timestampLocal, "%Y-%m-%d_%H-%M-%S_{}_spotlight.{}").format(
                        username, MEDIATYPES[mediaType]
                    )

                    if self.dumpJSON:
                        filename = os.path.join(dirname, Path(filename).stem + ".json")
                        mediaJSON = dict(snap)
                        mediaJSON["snapUser"] = userProfile
                        logger.opt(colors=True).info("\tDumping spotlight highlight JSON:\n\t\t<blue>{}</blue>".format(os.path.basename(filename)))
                        dumpResponse(mediaJSON, filename)

                    pathname = os.path.join(dirname, filename)
                    if self.noMultipart:
                        executor.submit(DownloadUrl, mediaURL, pathname, self.sleepInterval, self.quiet, self.automated, self.fast)
                    else:
                        if DownloadUrl(mediaURL, pathname, self.sleepInterval, self.quiet, self.automated, self.fast):
                            downloadCount += 1

        except KeyboardInterrupt:
            executor.shutdown(wait=False)

        snapCount = len(spotlightHighlights)
        msg = "{} spotlight highlights downloaded ({}) or existing ({}) for <magenta>{}</magenta>".format(snapCount, downloadCount, snapCount-downloadCount, username)
        if (downloadCount > 0):
            msg = "[✔] " + msg
        else:
            msg = "[-] " + msg
        if (downloadCount > 0):
            logger.opt(colors=True).success(msg)
        elif not self.automated:
            logger.opt(colors=True).info(msg)


    #----------------------------------------------------------------------------------------------------------------------
    def DownloadSnaps(self, username:str):
        """
        Download Snapchat snaps for `username`.

        Args:
            username (str): Snapchat `username`

        Returns:
            (none)
        """
    #----------------------------------------------------------------------------------------------------------------------
        logger.opt(colors=True).info("Calling Snapchat API for <magenta>{}</magenta>".format(username))
        retryCount = 0
        while retryCount < MAXRETRYCOUNT:
            retryCount += 1
            content, userProfile, publicStories, curatedHighlights, spotlightHighlights = self._apiProcessResponse(username)
            if content:
                break

        if not content:
            logger.opt(colors=True).error("[x] Unable to process Snapchat API results for <magenta>{}</magenta>\n".format(username))
            return

        displayname = self._findDisplayName(userProfile)
        userFolder = os.path.join(self.rootFolder, username)

        dumpResponse(content, os.path.join(userFolder, username+".json"))
        dumpResponse(userProfile, os.path.join(userFolder, username+"_user.json"))

        #download user avatar image
        if "linkPreview" in content["props"]["pageProps"]:
            linkPreview = content["props"]["pageProps"]["linkPreview"]
            if "facebookImage" in linkPreview:
                facebookImage = linkPreview["facebookImage"]
                url = facebookImage["url"]
                DownloadUrl(url, os.path.join(userFolder, displayname+".jpg"), sleepInterval=0, quiet=self.quiet, automated=self.automated, skipSizeCheck=self.fast)
        if "squareHeroImageUrl" in userProfile:
            url = userProfile["squareHeroImageUrl"]
            if len(url) > 0:
                DownloadUrl(url, os.path.join(userFolder, displayname+" (Hero).jpg"), sleepInterval=0, quiet=self.quiet, automated=self.automated, skipSizeCheck=self.fast)

        #download public stories
        if len(publicStories) > 0:
            dumpResponse(publicStories, os.path.join(userFolder, username+"_stories.json"))
            if not self.skipStories:
                self._downloadPublicStories(userProfile, publicStories)
        else:
            logger.opt(colors=True).info("\n[-] <magenta>{}</magenta> has no public stories".format(username))

        #download curated highlights
        if len(curatedHighlights) > 0:
            dumpResponse(curatedHighlights, os.path.join(userFolder, username+"_curated.json"))
            if not self.skipCurated:
                self._downloadCuratedHighlights(userProfile, curatedHighlights)
        else:
            logger.opt(colors=True).info("\n[-] <magenta>{}</magenta> has no curated highlights".format(username))

        #download spotlight highlights
        if len(spotlightHighlights) > 0:
            dumpResponse(spotlightHighlights, os.path.join(userFolder, username+"_spotlight.json"))
            if not self.skipSpotlight:
                self._downloadSpotlightHighlights(userProfile, spotlightHighlights)
        else:
            logger.opt(colors=True).info("\n[-] <magenta>{}</magenta> has no spotlight highlights".format(username))

        logger.opt(colors=True).info("\n[✔] Completed processing for <magenta>{}</magenta>\n".format(username))


#======================================================================================================================
#======================================================================================================================