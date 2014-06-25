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
#                  rev 2.0    10/09/2012
#                       - Created function NormalizeGuidString to replace the buggy RegFormatOutput pattern.
#                         Now all output GUIDs have a fixed length and are made uppercase
#
#                  rev 2.2    10/11/2012
#                       - Added list ExcludedDirs which folders will not be scanned
#                       - Added lambda function toU to conver registry format GUIDs to uppercase
#                       - Output filenames are now including timestamp strings
#                       - Logging filenames are always saved into a newly created file (suffixed with seq#)
#
#                  rev 3.0    10/11/2012
#                       - Added filter to remove some invalid lines in the output
#                       - Output lines are sorted and all duplicates removed
#
#                  rev 3.1    10/19/2012
#                       - Collected all user customizable values/configs into class UserConfig
#                       - Minor adjustment on summary output
#
#                  rev 3.2    10/25/2012
#                       - Modified Guid_In_h pattern to match wider range of GUID formats (in EDK)
#
#
#----------------------------------------------------------------------------------------------------
#
import os, re, string, sys
import logging
import datetime


#
# Global variables
#
class UserConfig:
  """ This class defines a set of constants and configurations which can be customized by 
      the script user. 
  """
  ScriptRev = " Ver 3.2"

  # To generate logging output, change this to 1
  LoggingEnable = 0

  # The maximum character width of the console output line
  MAXLINEWIDTH = 110

  # This list provides all the file types to be scanned
  TargetFileTypes = {'.h' : 0, '.dec' : 0, '.inf' : 0, '.dsc' : 0}

  # Directories to be excluded from the scan
  ExcludedDirs = ('.svn', 'Build', 'uefi64native')

  # Base file name for result output
  BaseOutputName = "guidxref_"

  # Base file name for logging output
  BaseLogName = ".\debug"



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
0x([0-9a-fA-F]+),\s*[{]*\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+),\s*\
0x([0-9a-fA-F]+)\s*[}]*\s*\}"

#This is buggy, has already been replaced by NormalizeGuidString2
RegFormatOutput = r"\1-\2-\3-\4\5-\6\7\8\9\10\11"   # Note: have to add prefix 'r' to make it raw here

# GUID Registry format - Below pattern matches lines like:  FILE_GUID = A5102DBA-C528-47bd-A992-A2906ED0D22B
Guid_In_Inf = "[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+-[0-9a-fA-F]+"


#################################### Functions Definition #################################################

def NormalizeGuidString (matchobj):
  """ Definitive format GUID string normalization - Prefixing with 0s for every captured group
      
      Parameter matchobj is a MatchObject instance which contains one or more subgroups of the pattern
      match done by the re.sub() method. It's same as the return object of re.search(). 
  """
  hex = [""]
  for i in range (1, 12):
    hex.append(matchobj.group(i))
  hex[1]  = format (int(hex[1],  16), '08x').upper()
  hex[2]  = format (int(hex[2],  16), '04x').upper()
  hex[3]  = format (int(hex[3],  16), '04x').upper()
  hex[4]  = format (int(hex[4],  16), '02x').upper()
  hex[5]  = format (int(hex[5],  16), '02x').upper()
  hex[6]  = format (int(hex[6],  16), '02x').upper()
  hex[7]  = format (int(hex[7],  16), '02x').upper()
  hex[8]  = format (int(hex[8],  16), '02x').upper()
  hex[9]  = format (int(hex[9],  16), '02x').upper()
  hex[10] = format (int(hex[10], 16), '02x').upper()
  hex[11] = format (int(hex[11], 16), '02x').upper()
  return hex[1]+'-'+hex[2]+'-'+hex[3]+'-'+hex[4]+hex[5]+'-'+hex[6]+hex[7]+hex[8]+hex[9]+hex[10]+hex[11]


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
      line = re.sub(RegGuidDef, filename + "  ", line)       # Trim out useless part
      line = re.sub(Guid_In_Inf, lambda toU: toU.group().upper(), line) # Convert GUID to uppercase
      #str = raw_input ("................................................. Press ENTER key to continue:")
      line = line.lstrip()
      line = re.sub("\A(.*?)\s+(.*)", r"\2  \1", line)       # Swap it. lx-'\A' and '?' are both important
      GuidLines.append(line)

    # Process .h and .dec files
    match = re.search(Guid_In_h, line, re.IGNORECASE | re.MULTILINE)
    if match:
      logging.debug ("Found a matching GUID")
      line = re.sub(DefineDirective, "", line)             # Trim out useless part
      line = re.sub(Guid_In_h, NormalizeGuidString, line) # Convert to registry format
      #str = raw_input ("................................................. Press ENTER key to continue:")
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
  if UserConfig.LoggingEnable:
    for seq in range (0, 99):
      LogFileName = UserConfig.BaseLogName + format (seq, '02d') + ".log"
      if not os.path.exists(LogFileName):
        break
      seq += 1
    logging.basicConfig(level=logging.INFO, filename=LogFileName, format='%(levelname)s: %(message)s')

  # Ensure input parameter is valid
  if len(sys.argv) < 2:
    print "Usage - ", sys.argv[0], " <Directory>\n"
    exit(0)

  RootDir = sys.argv[1]
  if (os.path.exists(RootDir) == False):
    print "Invalid directory name, please try again!"
    exit(1)
  
  # Determine output file
  now = datetime.datetime.now()
  suffix = now.strftime ("%Y_%m_%d_%H_%M_%S")

  ofile = open(UserConfig.BaseOutputName + suffix + ".txt", "w")
  # Print header message
  ofile.write("Generated by " + sys.argv[0] + UserConfig.ScriptRev + "\n")
  ofile.write("=" * 40 + "\n\n")

  # Traverse the root directory path for required source files
  TotalGuids = 0
  TempBuffer = []
  for root, dirs, files in os.walk(RootDir):
    # Check directories to be excluded from the scan
    for folder in UserConfig.ExcludedDirs:
      if folder in dirs:
        dirs.remove(folder)

    logging.debug ('  root = %s', root)
    #logging.debug ('  dirs = %s', dirs)
    #for file in files:
    #logging.debug ('  file = %s', file)
  
    for file in files:
      for type in UserConfig.TargetFileTypes.keys():
        if file.endswith(type):
          logging.info ("Found needed files = %s\\%s", root, file)
          UserConfig.TargetFileTypes[type] += 1

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
            OutputLineWidth = UserConfig.MAXLINEWIDTH - len(fullpath)
            print fullpath, "." * OutputLineWidth, len(GuidList)
            for line in GuidList:
              # Remove some invalid lines
              if not re.search (r"\/\/$", line, re.MULTILINE):    #lx: "\Z" and "\z" don't work. ??
                TempBuffer.append(line)

          ifile.close()

  # Remove duplicates from the list
  #
  # [Python.docs] A set object is an **unordered** collection of distinct hashable objects. Common uses 
  # include membership testing, removing duplicates from a sequence, and computing mathematical operations 
  # such as intersection, union, difference, and symmetric difference.
  #
  TempBuffer = list(set(TempBuffer))

  # Now sort the list
  #
  # [Python.docs] sorted (iterable [, key][, reverse])
  #
  #   key - specifies a function of one argument that is used to extract a comparison key from
  #         each list element: key=str.lower. The default value is None (compare the elements directly)
  #   reverse - a boolean value. If set to True, the list elements are sorted as if each comparison 
  #             were reversed.
  #
  TempBuffer = sorted(TempBuffer)
  for line in TempBuffer:
    TotalGuids += 1
    ofile.write(line)

  # Print summary
  print "\n", "-" * 50, "Summary", "-" * 55
  for type in UserConfig.TargetFileTypes.keys():
    print "Scanned ", format (UserConfig.TargetFileTypes[type], '04d'), format (type, "4s"), " files"

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

