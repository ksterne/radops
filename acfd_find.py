#!/usr/bin/env python

import os, sys
import tempfile
os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
import matplotlib
import pydarn
import datetime as dt
import datetime

#Defining radars I've already done. So we can skip these ones
completes = [ 'san' ]

def acfd_find_loop(sDate,radar):
	missing=0
	records=0
	eDate = sDate + datetime.timedelta(days=1)

	remote_fnamefmt = ['{date}.{hour}......{radar}.{ftype}','{date}.{hour}......{radar}...{ftype}']
	try: myPtr = pydarn.sdio.radDataOpen(sDate,radar,eDate,fileType='rawacf',local_fnamefmt=remote_fnamefmt,remote_fnamefmt=remote_fnamefmt)
	except Exception, e:
		print "problem with radDataOpen"
		print "sDate: %s  radar: %s  eDate: %s  " % (str(sDate), radar, str(eDate))
		print e
		sys.exit(-2)

	if(myPtr.dType == None): 
		print "No data found."
		return (-1, -1)

	print "Reading data..."
	myData = pydarn.sdio.radDataReadRec(myPtr)
	if(myData == None):
		print "Not able to read data."
		return (-2, -2)

	#for key in myData.prm.__dict__.keys():
	#	print 'myData.rawacf.'+key

		print "Searching through files for missing acfd arrays..."
	while (myData != None):
		try: array=myData.rawacf.acfd[0]
		except IndexError:
			missing += 1		
		records += 1		
		# Read in the next record
		myData = pydarn.sdio.radDataReadRec(myPtr)
	return (missing, records)

if __name__ == '__main__':

	radars = pydarn.radar.network()
	for iRad in xrange( radars.nradar ):
		sYear=2014
		eYear=2014
		if (radars.radars[iRad].status != 1):
			continue
		rad = radars.radars[iRad].code[0]
#		rad = 'sas'
		# Marking radars that we've completed for this month
		if rad in completes:
			continue
		while sYear >= eYear:
			sMonth=1
			eMonth=1
			while sMonth >= eMonth:
				# Reset missing and records for each new month
				missing=0
				records=0
				yrmnrad = str(sYear)+str(sMonth).zfill(2)+"."+rad
				sDay=31
				eDay=1
				while sDay >= eDay:
					fDate = str(sYear)+str(sMonth).zfill(2)+str(sDay).zfill(2)+"."+rad
#					sDate = dt.datetime(sYear,sMonth,sDay, 18, 00)
					sDate = dt.datetime(sYear,sMonth,sDay)
					miss, reco = acfd_find_loop(sDate, str(rad));
					if ( (miss < 0) or (reco < 0)):
						print "Did not find any data for "+str(rad)+" "+str(sDate)
						sDay -= 1
						continue
					if miss >= 0:
						missing+=miss
					if reco >= 0:
						records+=reco

					percentage = (float(missing)/float(records)) * 100
					
					print "missing: "+str(missing)
					print "records: "+str(records)
					print "percentage: %.3f percent" % (percentage)
					sDay -= 1
				print "Making: "+yrmnrad
				try: f = open(yrmnrad, 'w')
				except Exception, e:
					print e
					print "problem opening the file %s" % yrmnrad
					sys.exit(-1)
				# Case where no data was found for the month
				if ( records <= 0 ):
					percentage = 0
				f.write('Date: '+str(sYear)+str(sMonth).zfill(2)+str(sDay).zfill(2)+'\n')
				f.write('Total Number of Records: '+str(records)+'\n')
				f.write('Missing: '+str(missing)+'\n')
				f.write('Percentage: {:.3f}\n'.format(float(percentage)))
				sMonth -= 1
				f.close()

			sYear -= 1
		# Exit after just one radar
#		sys.exit(1)
	

