#############################################################################
# File		: rpmlint.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Mon Sep 27 19:20:18 1999
# Version	: $Id$
# Purpose	: main entry point: process options, load the checks and run
#		the checks.
#############################################################################

import sys
import AbstractCheck
import imp
import getopt
import Pkg
import Config
import os
import stat
import rpm
from Filter import *

version='0.36'

# Print usage information
def usage(name):
    print 'usage:', name, '[<options>] <rpm files>'
    print '  options in:'
    print '\t[-i|--info]\n\t[-c|--check <check>]\n\t[-a|--all]\n\t[-C|--checkdir <checkdir>]\n\t[-h|--help]\n\t[-v|--verbose]\n\t[-E|--extractdir <dir>]\n\t[-p|--profile]\n\t[-V|--version]'

# Print version information
def printVersion():
    print 'rpmlint version', version, 'Copyright (C) 1999-2001 Frederic Lepied, MandrakeSoft'

# Load a python module from its file name
def loadCheck(name):	
    (file, pathname, description)=imp.find_module(name, Config.checkDirs())
    imp.load_module(name, file, pathname, description)

# Load a file
def loadFile(name):
    file=os.fdopen(os.open(os.path.expanduser(name), os.O_RDONLY))
    imp.load_source('', name, file)
    
#############################################################################
# main program
#############################################################################
def main():
    # Load all the tests
    for c in Config.allChecks():
        loadCheck(c)
    
    try:
        # Loop over all file names given in arguments
        for f in args:
            try:
                try:
                    st=os.stat(f)
                    if not stat.S_ISREG(st[stat.ST_MODE]):
                        raise OSError
                    pkg=Pkg.Pkg(f, extract_dir)
                except OSError:
                    pkg=Pkg.InstalledPkg(f)
            except:
                sys.stderr.write('Error while reading ' + f + '\n')
                pkg=None
                continue
        
            if verbose:
                printInfo(pkg, 'checking')

            for c in AbstractCheck.AbstractCheck.checks:
                c.check(pkg, verbose)                

            pkg.cleanup()

        # if requested, scan all the installed packages
        if all:
            db=rpm.opendb()
            idx=db.firstkey()
            while idx:
                pkg=Pkg.InstalledPkg(db[idx][rpm.RPMTAG_NAME], db[idx])
                
                if verbose:
                    printInfo(pkg, 'checking')

                for c in AbstractCheck.AbstractCheck.checks:
                    c.check(pkg, verbose)

                pkg.cleanup()

                idx=db.nextkey(idx)
            del db

    finally:
        pkg and pkg.cleanup()

#############################################################################
# 
#############################################################################
sys.argv[0] = os.path.basename(sys.argv[0])

# parse options
try:
    (opt, args)=getopt.getopt(sys.argv[1:], 'ic:C:hVvp:anE:', ['info',
                                                              'check=',
                                                              'checkdir=',
                                                              'help',
                                                              'version',
                                                              'verbose',
                                                              'profile',
                                                              'all',
                                                              'noexception',
                                                              'extractdir='])
except getopt.error:
    print 'bad option'
    usage(sys.argv[0])
    sys.exit(1)

# process options
checkdir='/usr/share/rpmlint'
verbose=0
extract_dir=Config.getOption('ExtractDir', '/tmp')
prof=0
all=0

# load global config file
try:
    loadFile('/etc/rpmlint/config')
except OSError:
    pass

# load user config file
try:
    loadFile('~/.rpmlintrc')
except OSError:
    pass

# process command line options
for o in opt:
    if o[0] == '-c' or o[0] == '--check':
	Config.addCheck(o[1])
    elif o[0] == '-i' or o[0] == '--info':
        Config.info=1
    elif o[0] == '-h' or o[0] == '--help':
	usage(sys.argv[0])
	sys.exit(0)
    elif o[0] == '-C' or o[0] == '--checkdir':
	Config.addCheckDir(o[1])
    elif o[0] == '-v' or o[0] == '--verbose':
	verbose=1
    elif o[0] == '-V' or o[0] == '--version':
	printVersion()
	sys.exit(0)
    elif o[0] == '-E' or o[0] == '--extractdir':
	extract_dir=o[1]
        Config.setOption('ExtractDir', extract_dir)
    elif o[0] == '-p' or o[0] == '--profile':
        prof=o[1]
    elif o[0] == '-n' or o[0] == '--noexception':
        Config.no_exception=1
    elif o[0] == '-a' or o[0] == '--all':
        all=1
    else:
	print 'unknown option', o

# if no argument print usage
if args == [] and not all:
    usage(sys.argv[0])
    sys.exit(0)

if prof:
    import profile
    import pstats
    profile.run('main()', prof)
    p = pstats.Stats(prof)
    p.print_stats('time').print_stats(20)
else:
    main()

# rpmlint.py ends here
