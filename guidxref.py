#!/c:\python27\python.exe
#
#      Filename:   guidxref.py
#       Written:   Xiang Lian
#
#
# This python script scans through UDK2010 build tree and saves all GUID definitions into
# an output file. Refer list TargetFileTypes for currently suported source file types.
#
#-------------------------------------------------------------------------------------------------
#
#   Rev history:   rev 1.0    10/07/2012
#                       - Guid_In_h had missed some lower-cased GUIDs;
#
#                  rev 1.1    10/07/2012
#                       - Added captured groups in Guid_In_h, refer RegFormatOutput;
#
#                  rev 1.2    10/08/2012
#                       - Swapped content in output line so that GUID strings always come first
#
#                  rev 1.5    10/08/2012
#                       - Simplified os.walk logic to significantly reduce the redundant scans
#                       - Added summary to report total number of files scanned by type
#
#                  rev 1.6    10/08/2012
#                       - Added logging module, to turn on logging output:
#                             . Uncomment the logging.basicConfig line
#                             . Choose level in basicConfig
#                       - Always save result into a newly create output file
#
#
#
#
#----------------------------------------------------------------------------------------------------
#
import os, re, string, sys
import logging


#
# Global variables
#

# This list provides all the file types to be scanned
TargetFileTypes = {'.h' : 0, '.dec' : 0, '.inf' : 0, '.dsc' : 0}

# This defines the continuation character at end of line
ContinuingEol = "\\\n"

# Define directive in GUID definition (usually in .h files)
DefineDirective = "^#define"

# Header part of the GUID definition line (usually in INF or DSC files)
RegGuidDef = "^.*\=\s*"          #note: "^\(.*\)\=\s*" doesn't work!

# GUID Definitive format - Below pattern matches lines like: 
#      { 0xbf9d5465, 0x4fc3, 0x4021, {0x92, 0x5, 0xfa, 0x5d, 0x3f, 0xe2, 0xa5, 0x95}}
Guid_In_h = "\{\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\{\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+)\s*\}\s*\}"

RegFormatOutput = r"\1-\2-\3-\4\5-\6\7\8\9\10\11"   # Note: have to add prefix 'r' to make it raw here

# GUID Registry format - Below pattern matches lines like:  FILE_GUID = A5102DBA-C528-47bd-A992-A2906ED0D22B
Guid_In_Inf = "[0-9A-F]+-[0-9A-F]+-[0-9A-F]+-[0-9A-F]+-[0-9A-F]+"


#################################### Functions Definition #################################################

def SearchGuidsFromList (SrcList, filename):
  """ This function searchs for GUID definitions from a given string list.

  """
  GuidLines = []
  for n,line in enumerate(SrcList):
    while line.endswith(ContinuingEol):
      line = line.rstrip(ContinuingEol)
      #this doesnt work?? line = re.sub("\\\n", "", line)
      MergeLine = [line, SrcList[n+1]]
      line = "".join(MergeLine)      # This converts a list to a string
      del SrcList[n+1]
      #logging.debug ("  Merged line #%d, %s", n, line)
  
    # Now start searching for GUID pattern
    #lx-We do not need to match this as it's within a single line now.
    #lx match0 = re.search(DefineDirective, line, re.IGNORECASE | re.MULTILINE)
    #lx if match0:

    # Process .inf and .dsc files
    match = re.search(Guid_In_Inf, line, re.IGNORECASE | re.MULTILINE)
    if match:
      logging.debug ("Found a matching GUID")
      line = re.sub(RegGuidDef, filename + "  ", line)    # Trim out useless part
      line = line.lstrip()
      line = re.sub("\A(.*?)\s+(.*)", r"\2  \1", line)    # Swap it. lx-'\A' and '?' are both important
      GuidLines.append(line)
      #debug str = raw_input ("................................................. Press ENTER key to continue:")

    # Process .h and .dec files
    match = re.search(Guid_In_h, line, re.IGNORECASE | re.MULTILINE)
    if match:
      logging.debug ("Found a matching GUID")
      line = re.sub(DefineDirective, "", line)            # Trim out useless part
      line = re.sub(Guid_In_h, RegFormatOutput, line)     # Convert to registry format
      line = line.lstrip()
      line = re.sub("\A(.*?)[ =]+(.*)", r"\2  \1", line)  # Swap it. lx-'\A' and '?' are both important
      GuidLines.append(line)

  return GuidLines


def main():

  # Configure the logging module to send debug messages to file
  #
  # Refer:
  #    logging.debug (msg, *args)
  #    logging.info (msg, *args)
  #    logging.warning (msg, *args)
  #    logging.error (msg, *args)
  #    logging.critical (msg, *args)
  #    logging.setLevel (level)
  #    logging.disable (level)
  #
  # Valid values to set for level (by severity) in basicConfig are: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
  #
  #full format: logging.basicConfig(level=logging.DEBUG, filename='debug.log', format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
  #logging.basicConfig(level=logging.ERROR, filename='debug.log', format='%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

  # Ensure input parameter is valid
  if len(sys.argv) < 2:
    print "Usage - ", sys.argv[0], " <Directory>\n"
    exit(0)

  RootDir = sys.argv[1]
  if (os.path.exists(RootDir) == False):
    print "Invalid directory name, please try again!"
    exit(1)
  
  # Determine output file
  for x in range (0, 99):
    OutputFileName = ".\guidref" + format (x, '02d') + ".txt"
    if not os.path.exists(OutputFileName):
      break
    x += 1

  ofile = open(OutputFileName, "w")

  # Traverse the folder path and search for required source files
  TotalGuids = 0
  for root, dirs, files in os.walk(RootDir):
    logging.debug ('  root = %s', root)
    #logging.debug ('  dirs = %s', dirs)
    #for file in files:
    #logging.debug ('  file = %s', file)
  
    for file in files:
      for type in TargetFileTypes.keys():
        if file.endswith(type):
          logging.info ("Found needed files = %s\\%s", root, file)
          TargetFileTypes[type] += 1

          # Scan the file for GUID strings
          try:
            fullpath = os.path.join(root, "".join(file))
            ifile = open(fullpath, "r")
          except:
            print folder, "\\", file, " could not be opened, abort!"
            sys.exit(2)
          
          logging.debug ('Opening source file ........%s', fullpath)
          AllLines = ifile.readlines()
          GuidList = SearchGuidsFromList (AllLines, "".join(file))
          if (len(GuidList) > 0):
            OutputLineWidth = 110 - len(fullpath)
            print fullpath, "." * OutputLineWidth, len(GuidList)
            TotalGuids += len(GuidList)
            for line in GuidList:
              ofile.write(line)
          
          ifile.close()

  # Print summary
  print "\n", "-" * 50, "Summary", "-" * 55
  for type in TargetFileTypes.keys():
    print "File type: ", type, TargetFileTypes[type], "files"

  print "\nTotal number of GUIDs found: ", TotalGuids 


#
# Why do we need this?
# A .py file can be interpreted by Python as either standalone program to execute directly,
# or a module to be imported into other .py files. 
#   1) Standalone program - __name__ equals to "__main__"; 
#   2) imported as a module - __name__ equals to something else, therefore contents behind
#      the if statement won't get executed.
#
if __name__ == "__main__":
  main()

