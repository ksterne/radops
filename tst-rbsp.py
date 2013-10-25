#This script reads off the Dst Kyoto index from the website and makes a decision
#about whether or not the triggered mode needs to be written to the special
#schedule file.

import urllib
from HTMLParser import HTMLParser
import string
from datetime import timedelta
import datetime
import os
import time
import ftplib

command={}
default_priority=15
max_duration=360
radars=["tst"]
command["tst"]="rbspscan4 -westbm 10 -meribm 11 -eastbm 13"
scddir="/data/scd/"
basescdfile="special.scd"
ref_hours=1
Dst_onset_threshold= -50
Dst_end_threshold=-30
Dst_active=False

class MyHTMLParser(HTMLParser):
    active=False 
    table=None
    def handle_comment(self,data):
        if data.strip()==' ^^^^^ E yyyymm_part2.html ^^^^^ '.strip():
          self.active=True
        else:
    	  if self.active==True:
	    pass 
          self.active=False 
    def handle_data(self, data):
        if self.active:
          self.table=data

current_time=datetime.datetime.utcnow()
print "Current Time:", current_time
entry_endtime=current_time-datetime.timedelta(days=1)
reference_time=current_time-datetime.timedelta(seconds=60*60*ref_hours)
timestr="%04d%02d" % (reference_time.year,reference_time.month)

print "Dst onset threshold: %lf" % (Dst_onset_threshold)
print "Dst end threshold: %lf" % (Dst_end_threshold)
# Wait 20 seconds in case of any updating lags on the Kyoto site
print "Waiting 20 seconds..."
time.sleep(20)
# Now lets grab the Dst info
opener = urllib.FancyURLopener({})
print "Using URL: ","http://wdc.kugi.kyoto-u.ac.jp/dst_realtime/%s/index.html" % (timestr)
f = opener.open("http://wdc.kugi.kyoto-u.ac.jp/dst_realtime/%s/index.html" % (timestr))
text=f.read()
parser = MyHTMLParser()
parser.feed(text)
lines=parser.table.split("\n")
for line in lines[7:]:
    try:
      dy=int(line[0:2])
    except ValueError:
      dy=0
    if dy==reference_time.day:
	# Updated way to find the hour from BAS engineer
        time=datetime.datetime.utcnow() - timedelta(minutes=30)
        hour=time.hour
	hour_offset= (hour*4) + divmod(hour,8)[0] + 3
	
#        hour=reference_time.hour+1
#        offset=-1;
#        if hour>8:
#          offset=offset+1
#        if hour>16:
#          offset=offset+1 
	# Update from BAS engineer 
 	ref_Dst=line[hour_offset:hour_offset+4]
 #        ref_Dst=line[offset+hour*4:4+offset+hour*4]    
        ref_Dst=int(ref_Dst)
#      print "Reference Dst Hour: %d Val: %d" % (hour,ref_Dst) 
        print "Day: %d Hour: %d  Dst value: %lf" % (dy,hour,ref_Dst)

# Read existing RSBP schedule file and find ongoing event if it exists
for radar in radars:
  scdfilename="%s-%s" % (radar,basescdfile)
  scdfile=os.path.join(scddir,scdfilename)
  print scdfile
  if os.path.exists(scdfile):
    f = open(scdfile, 'r+')
    lines=f.readlines()
    f.close()
    next_line=False
    fallback_duration=max_duration
    for line in lines:
      if next_line:
        next_line=False
        segments=line.split()
        yr=int(segments[0].strip()) 
        mo=int(segments[1].strip()) 
        dy=int(segments[2].strip()) 
        hr=int(segments[3].strip()) 
        mi=int(segments[4].strip()) 
        try:
          dur=int(segments[5].strip()) 
        except ValueError:
          dur=fallback_duration
        prio=int(segments[6].strip()) 
        entry_endtime=datetime.datetime(yr,mo,dy,hr,mi)+datetime.timedelta(seconds=60*dur)
      if "::ACTIVE::" in line:
        val=line.split("::ACTIVE::")[1].strip()
        Dst_active={"true": True, "false": False}.get(val.lower())
      if "duration" in line:
        fallback_duration=int(line.split("duration")[1].strip())
      if "::CURRENT_EVENT:" in line:
        next_line=True


# Logic for new or ongoing event handling
  if Dst_active:
    if ref_Dst < Dst_end_threshold:
      print "Reset Ongoing Event Duration"
      write_entry=True
    else:
      print "Tailing Event trigger"
      write_entry=False
      #Added Dst_active line to correct logic.  As soon as the Dst_end_threshold has
      #been crossed on the up-swing, the triggered mode should end.
      Dst_active=False
      if(entry_endtime < current_time):
        print "Event trigger has expired"
        Dst_active=False
        write_entry=False
  else:
    if ref_Dst < Dst_onset_threshold:
      print "New Event trigger"
      Dst_active=True
      write_entry=True
    else:
      print "No event :: Current Dst: %lf" % (ref_Dst)
      Dst_active=False
      write_entry=False

# Write new scdfile
  print "Updating %s" %(scdfile)
 
  lines=[]
  lines.append("# RSBP Triggered Event Schedule")
  lines.append("#   This is an automated generated schedule,")
  lines.append("#   please do not edit by hand")
  lines.append("#")
  lines.append("# ::ACTIVE:: %s"% (Dst_active))
  lines.append("# ::UPDATED:: %s"% (current_time))
  lines.append("#")
  lines.append("")
  lines.append("priority %d" % (default_priority))
  lines.append("duration %d" % (max_duration))
  lines.append("")
  lines.append("# ::CURRENT_EVENT: ")
  if write_entry:
    datestr="%04d %02d %02d %02d %02d" % (current_time.year,current_time.month,current_time.day,current_time.hour,current_time.minute)
    prestr="%s %02d %02d" % (datestr,max_duration,default_priority)
    lines.append("%s %s" % (prestr,command[radar]))

  f = open(scdfile, 'w+')
  for line in lines:
    f.write(line+"\n")
  f.close()

sftp=ftplib.FTP('QNX4 IP ADDRESS','username','PASS')
#Change working directory to scddir
sftp.cwd(scddir)
#Connect
fp=open(scdfile, 'rb') #file to send to main QNX computer
sftp.storbinary('STOR radar-special.scd', fp) #sends the file
fp.close() #Close the file and ftp
sftp.quit()

