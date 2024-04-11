#!/bin/bash

usage() {
	echo "Usage: $0 [elf executable] [pami/act/ass/hat/extra/custom] (swc pin) (swd pin)"
	exit 1
}

if [ $# -lt 1 ]; then
	echo "You need to specify the file to flash"
	usage
fi

if [ $# -lt 2 ]; then
	echo "You need to specify the pico to flash"
	usage
fi

case "$2" in
	pami)
		swc=26
		swd=19
		;;

	act)
		swc=5
		swd=0
		;;

	ass)
		swc=10
		swd=9
		;;

	hat)
		swc=13
		swd=6
		;;

	extra)
		swc=5
		swd=0
		;;

	custom)
		if [ $# -lt 4 ]; then
			echo "You need to specify the SWC and SWC pins for the custom mode"
			usage
		fi
		swc="$3"
		swd="$4"
		;;

	*)
		echo "'$2' is not a valid pico"
		usage
		;;
esac

file="$1"

if [ ! -f "$file" ]; then
	echo "File '$file' doesn't exist"
	exit 1
fi 

echo "Flashing '$file'"
echo "Using pins: swc=$swc swd=$swd"
echo ""

openocd -d1 -f /usr/share/openocd/scripts/interface/raspberrypi2-native.cfg -c "bcm2835gpio swd_nums $swc $swd; adapter_khz 1000" -f /usr/share/openocd/scripts/target/rp2040.cfg \
	-c "program $file verify ; init ; reset halt ; rp2040.core1 arp_reset assert 0 ; rp2040.core0 arp_reset assert 0; exit"
