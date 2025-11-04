<p>
  <div align="center">
  <h1>
    Snapchat Public Stories Downloader<br /> <br />
    <a href="https://pypi.python.org/pypi/snapchat-dl">
      <img
        src="https://img.shields.io/pypi/v/snapchat-dl.svg?cacheSeconds=360"
        alt="Python Package"
      />
    </a>
    <a href="https://pypi.python.org/pypi/snapchat-dl">
      <img
        src="https://img.shields.io/pypi/wheel/snapchat-dl"
        alt="Python Wheel"
      />
    </a>
    <a href="https://pypi.python.org/pypi/snapchat-dl">
      <img
        src="https://img.shields.io/github/actions/workflow/status/stevehoek/snapchat-dl/continuous-integration-pip.yml?cacheSeconds=360"
        alt="CI"
      />
    </a>
    <a href="https://codecov.io/gh/stevehoek/snapchat-dl">
      <img
        src="https://img.shields.io/codecov/c/github/stevehoek/snapchat-dl?cacheSeconds=360"
        alt="Code Coverage"
      />
    </a>
    <a href="https://codecov.io/gh/stevehoek/snapchat-dl">
      <img
        src="https://img.shields.io/pypi/pyversions/snapchat-dl"
        alt="Python Versions"
      />
    </a>
    <a href="https://github.com/psf/black">
      <img
        src="https://img.shields.io/badge/code%20style-black-000000.svg"
        alt="The Uncompromising Code Formatter"
      />
    </a>
    <a href="https://pepy.tech/project/snapchat-dl">
      <img
        src="https://static.pepy.tech/badge/snapchat-dl"
        alt="Monthly Downloads"
      />
    </a>
    <a href="https://opensource.org/licenses/MIT">
      <img
        src="https://img.shields.io/badge/License-MIT-blue.svg"
        alt="License: MIT"
      />
    </a>
  </h1>
  </div>
</p>

### Installation

Install using pip,

```bash
pip install snapchat-dl
```

Install from GitHub,

```bash
pip install git+git://github.com/stevehoek/snapchat-dl
```

Unix users might want to add `--user` flag to install without requiring `sudo`.

### Usage

```text

usage: snapchat-dl [-h] [-r ROOTFOLDER] [-f] [-b BATCHFILE] [-c | -u] [-ss]
                   [-sc] [-sh] [-d] [-g] [-nm] [-w MAXWORKERS]
                   [-ui UPDATEINTERVAL] [-si SLEEPINTERVAL] [-fast] [-q] [-a]
                   [username ...]

positional arguments:
  username              One or more usernames to download content for.

options:
  -h, --help            show this help message and exit
  -r, --root-folder ROOTFOLDER
                        Location to store downloaded content.
  -f, --scan-root-folder
                        Scan usernames (as folder name) from root folder.
  -b, --scan-batch-file BATCHFILE
                        Read usernames from batch file (one username per
                        line).
  -c, --scan-clipboard  Scan clipboard for story links
                        ('https://story.snapchat.com/<s>/<username>').
  -u, --check-for-update
                        Periodically check for new content.
  -ss, --skip-stories   Skip downloading public stories.
  -sc, --skip-curated   Skip downloading curated highlights.
  -sh, --skip-spotlight
                        Skip downloading spotlight highlights.
  -d, --dump-json       Save snap metadata to a JSON file next to downloaded
                        content.
  -g, --generate-scripts
                        Generate shell scripts for combining multipart
                        stories.
  -nm, --no-multipart   Don't combine multipart stories.
  -w, --max-workers MAXWORKERS
                        Set maximum number of parallel downloads. (Default: 4)
                        NOTE: only applies when --no-multipart arg is present
  -ui, --update-interval UPDATEINTERVAL
                        Set the update interval for checking new content in
                        seconds. (Default: 600s)
  -si, --sleep-interval SLEEPINTERVAL
                        Sleep between downloads in seconds. (Default: 1s)
  -fast, --fast         Skip online size checks for snap media.
  -q, --quiet           Do not print anything but errors to the console.
  -a, --automated       Change logging style when run under automation (eg:
                        Shortcuts).

```
