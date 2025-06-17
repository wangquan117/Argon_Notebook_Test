#!/bin/bash

checkhdparm=$(dpkg-query -W -f='${Status}\n' "hdparm" 2> /dev/null | grep "installed")
if [ "" == "$checkhdparm" ]; then
	echo "Installing hdparm"
	sudo apt-get install -y hdparm
fi

DEFAULTWRITEMODE=1 # 0 wipe MBR; 1 Try mount point; 2 skip

bootdrive=`df | grep '/boot'| awk '{print $1}'`

list=`lsblk | grep -e '0 disk' | awk '{print $1}'`
for hd in $list
do
		hddsize=`lsblk | grep -e '0 disk' | grep $hd | awk '{print $4}'`
		hddunit=${hddsize: -1}
		hddcheck=`cut -d "." -f1 <<< $hddsize `
		hddchecklen=${#hddcheck}
		if [ "$hddunit" == "G" ]
		then
			hddchecklen=$[hddchecklen+9]
		elif [ "$hddunit" == "T" ]
		then
			hddchecklen=$[hddchecklen+12]
		elif [ "$hddunit" == "M" ]
		then
			hddchecklen=$[hddchecklen+6]
		fi

		if [ $hddchecklen -lt 12 ]
		then
			echo "$hd:$hddsize Skipped Tests"
			continue
		fi

		curdev="/dev/$hd"

		# Read Test	
		#echo "Read Test"
		readingspeed=`sudo hdparm --direct -t $curdev | grep Timing | awk '{print $(NF-1)$NF}'`
		readcheck=`cut -d "." -f1 <<< $readingspeed `
		readchecklen=${#readcheck}

		mountpath=""
		writemode=$DEFAULTWRITEMODE
		if [[ $bootdrive == *$hd* ]]
		then
			# Boot drive
			writemode=1
			mountpath="/"
		fi

		# Write Test
		writesize="256MB"
		if [ $readchecklen -lt 3 ]
		then
			writesize="64MB"
			writemode=2
		fi

		#echo "Write Test"
		if [ $writemode -eq 0 ]
		then
			# WARNING: This destroys MBR!!!
			writespeed=`sudo dd if=/dev/zero of=$curdev bs=$writesize count=1 2>&1 | grep -v ecords | awk '{print $(NF-1)$NF}'`
		elif [ $writemode -eq 1 ]
		then
			if [ "$mountpath" == "" ]
			then
				# Get first mount point
				mountpath=`cat /proc/mounts | grep $curdev | head -n 1 | awk '{print $2}'`
				if [ "$mountpath" != "" ]
				then
					mountpath="$mountpath/"
				fi
			fi
			if [ "$mountpath" == "" ]
			then
				# No mount point found
				writespeed="N/A"
			else
				testfile=`echo ${mountpath}writetest.img | sed 's/\\\\040/ /g' | sed 's/\\\\011/\t/g'`
				sudo touch "$testfile" 2> /dev/null
				if [ -f $testfile ]
				then
					writespeed=`sudo dd if=/dev/zero of="$testfile" bs=$writesize count=1 oflag=dsync 2>&1 | grep -v ecords | awk '{print $(NF-1)$NF}'`
					sudo rm "$testfile"
				else
					# No mount point found
					writespeed="N/A"
				fi
			fi
		else
			writespeed="Skipped"
		fi
		echo "$hd:$hddsize Read:$readingspeed Write:$writespeed"
done

