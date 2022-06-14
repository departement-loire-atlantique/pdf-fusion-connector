# https://github.com/revolunet/pypdftk/blob/master/pypdftk.py

import logging
import os
import subprocess
import tempfile

log = logging.getLogger(__name__)

if os.getenv("PDFTK_PATH"):
    PDFTK_PATH = os.getenv("PDFTK_PATH")
else:
    PDFTK_PATH = "/usr/bin/pdftk"
    if not os.path.isfile(PDFTK_PATH):
        PDFTK_PATH = "pdftk"


def check_output(*popenargs, **kwargs):
    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output


def run_command(command, shell=False):
    """run a system command and yield output"""
    p = check_output(command, shell=shell)
    return p.decode("utf-8").splitlines()


try:
    run_command([PDFTK_PATH])
except OSError:
    logging.warning("pdftk test call failed (PDFTK_PATH=%r).", PDFTK_PATH)


def concat(files, out_file=None, output_pdf=None):
    '''
        Merge multiples PDF files.
        Return temp file if no out_file provided.
    '''
    cleanOnFail = False
    handle = None
    if not out_file:
        cleanOnFail = True
        handle, out_file = tempfile.mkstemp(dir=output_pdf)
        
    cmd = "%s %s cat output %s" % (PDFTK_PATH, ' '.join(files), out_file)
    try:
        run_command(cmd,True)
    except:
        if cleanOnFail:
            os.remove(out_file)
        raise
    finally:
        if handle:
            os.close(handle)

    return out_file