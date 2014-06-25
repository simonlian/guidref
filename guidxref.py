#!/c:\python27\python.exe
#
#      Filename:   guidxref.py
#       Written:   Xiang Lian
#   Rev history:   rev 1.0    10/07/2012
#                       - Guid_In_h had missed some lower-cased GUIDs;
#
#                  rev 1.1    10/07/2012
#                       - Added captured groups in Guid_In_h, refer RegFormatOutput;
#
#####################################################################################################
#
# This is my first hands-on exercise of Python language learning.
#
# This python script scans through UDK2010 build tree and saves all GUID definitions into
# an output file. Refer list TargetFileTypes for currently suported source file types.
#
#
import os, re, string, sys


#
# Global variables
#

# This list provides all the file types to be scanned
TargetFileTypes = ['.h', '.dec', '.inf', '.dsc']

# This defines the continuation character at end of line
ContinuingEol = "\\\n"

# Define directive in GUID definition (usually in .h files)
DefineDirective = "^#define"

# Header part of the GUID definition line (usually in INF or DSC files)
RegGuidDef = "^.*\=\s*"          #lx-note: "^\(.*\)\=\s*" doesn't work!

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
      #print "line #n", n,line
      #print "line #n+1", n+1,SrcList[n+1]
  
    # Now start searching for GUID pattern
    #lx-We do not need to match this as it's within a single line now.
    #lx match0 = re.search(DefineDirective, line, re.IGNORECASE | re.MULTILINE)
    #lx if match0:

    # for INF and DSC files
    match = re.search(Guid_In_Inf, line, re.IGNORECASE | re.MULTILINE)
    if match:
      #print "Found a matching GUID line"
      line = re.sub(RegGuidDef, filename + "  ", line)     # Trim out useless part
      line = line.lstrip()
      GuidLines.append(line)
      #debug str = raw_input ("Press ENTER key to continue:")

    # for .h file
    match = re.search(Guid_In_h, line, re.IGNORECASE | re.MULTILINE)
    if match:
      #print "Found a matching GUID line"
      line = re.sub(DefineDirective, "", line)     # Trim out useless part
      line = re.sub(Guid_In_h, RegFormatOutput, line)     # Trim out useless part
      line = line.lstrip()
      GuidLines.append(line)

  return GuidLines


def main():

  # Ensure input parameter is valid
  if len(sys.argv) < 2:
    print "Usage - ", sys.argv[0], " <Directory>\n"
    exit(0)

  RootDir = sys.argv[1]
  if (os.path.exists(RootDir) == False):
    print "Invalid directory name, please try again!"
    exit(1)
  
  # Traverse the folder path and search for required source files
  SearchFileDb = {}       # This is a database of dir:files pairs
  for root, dirs, files in os.walk(RootDir):
    if '.svn' in dirs:
      dirs.remove('.svn') 
    #print "root = ", root
    #print "dirs = ", dirs
    SearchFileDb[root] = files
  
    for Dir in SearchFileDb:
      ChosenFiles = []
      for file in SearchFileDb[Dir]:
        for type in TargetFileTypes:
          if file.endswith(type):
            #print "Found needed files = ", file
            ChosenFiles.append(file)
      SearchFileDb[Dir] = ChosenFiles
  
  #print "Dict =", SearchFileDb
  #print "Dict keys()=", SearchFileDb.keys()
  #print "Dict values()=", SearchFileDb.values()
  
  # Create output file
  ofile = open("guidxref.txt", "w")

  # Search for qualified GUID lines in each file
  TotalGuids = 0
  for folder in SearchFileDb.keys():           # equivalent of looping through SearchFileDb
    for file in SearchFileDb[folder]:
      #print "Search folder=", folder
      #print "Search file=", file
      try:
        fullpath = os.path.join(folder, "".join(file))
        ifile=open(fullpath, "r")
      except:
        print folder, "\\", file, " could not be opened, abort!"
        sys.exit(2)
  
      AllLines = ifile.readlines()
      GuidList = SearchGuidsFromList (AllLines, "".join(file))
      if (len(GuidList) > 0):
        OutputLineWidth = 100 - len(fullpath)
        print fullpath, "." * OutputLineWidth, len(GuidList)
        TotalGuids = TotalGuids + len(GuidList)
        for line in GuidList:
          ofile.write(line)
  
      ifile.close()
  print "Total of GUIDs found: ", TotalGuids 



#lx-Why do I need this?
if __name__ == "__main__":
		main()

