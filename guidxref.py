#!/c:\python27\python.exe
#
#file_io.py

import os, re, string, sys


#
# Global variables
#
ContinueEol = "\\\n"
DefineGuid  = "#define"
Guid_In_h   = "\{\s*0x([0-9A-F])+,\s*0x([0-9A-F])+,\s*0x([0-9A-F])+,\s*\{\s*0x([0-9A-F])+,\s*0x([0-9A-F])+,\
\s*0x([0-9A-F])+,\s*0x([0-9A-F])+,\s*0x([0-9A-F])+,\s*0x([0-9A-F])+,\s*0x([0-9A-F])+,\s*0x([0-9A-F])+\s*\}\s*\}"



def SearchGuidsFromList (SrcList):
  """ This function searchs for GUID definitions from a given string list.

  """
  GuidLines = []
  for n,line in enumerate(SrcList):
    while line.endswith(ContinueEol):
      line = line.rstrip(ContinueEol)
      #this doesnt work?? line = re.sub("\\\n", "", line)
      MergeLine = [line, SrcList[n+1]]
      line = "".join(MergeLine)
      del SrcList[n+1]
      #print "line #n", n,line
      #print "line #n+1", n+1,SrcList[n+1]
  
    # Now start searching for GUID pattern
    match1 = re.search(DefineGuid, line, re.I | re.M)
    if match1:
      match2 = re.search(Guid_In_h, line, re.I | re.M)
      if match2:
        #print "Find a matching GUID line"
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
        if file.endswith(".h"):
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
        print folder, "\\", file, " could not be opened!"
        sys.exit(2)
  
      AllLines = ifile.readlines()
      GuidList = SearchGuidsFromList (AllLines)
      if (len(GuidList) > 0):
        OutputLineWidth = 90 - len(fullpath)
        print fullpath, "." * OutputLineWidth, len(GuidList)
        TotalGuids = TotalGuids + len(GuidList)
        for line in GuidList:
          ofile.write(line)
  
      ifile.close()
  print "Total of GUIDs found: ", TotalGuids 




if __name__ == "__main__":
		main()

