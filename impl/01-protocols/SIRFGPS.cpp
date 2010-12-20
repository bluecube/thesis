#include "SIRFGPS.h"

#include <assert.h>
#include <err.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * Open the serial port, find out GPS mode.
 */
SIRFGPS::SIRFGPS(const char *device, unsigned speed){
	port.open(device, speed);
	
	while(true){
		if(check_mode() != GPS_MODE_UNKNOWN){
			break;
		}
	}

	permanent_mode();

	while(!switch_mode(GPS_MODE_SIRF, 4800));
}

/**
 * Restore the old gps mode.
 */
SIRFGPS::~SIRFGPS(){
	restore_mode();
}

/**
 * Try parsing both NMEA and SIRF protocols and return
 * which one was found.
 * Also sets the global mode flag.
 */
enum SIRFGPS::GPSMode SIRFGPS::check_mode(){
	port.drop_unread();

	if(nmea.parse(&port)){
		mode = GPS_MODE_NMEA;
		printf("GPS receiver is in NMEA 0183 mode.\n");
	}else if(sirf.parse(&port)){
		printf("GPS receiver is in SIRF mode.\n");
		mode = GPS_MODE_SIRF;
	}else{
		printf("GPS receiver is in unknown mode.\n");
		mode = GPS_MODE_UNKNOWN;
	}

	return mode;
}

void SIRFGPS::get_one(){
	if(mode == GPS_MODE_NMEA){
		nmea.parse(&port);
	}else if(mode == GPS_MODE_SIRF){
		sirf.parse(&port);
	}else{
		warnx("Cant read messages in unknown mode.");
		return;
	}
}


bool SIRFGPS::switch_mode(SIRFGPS::GPSMode desiredMode, unsigned speed){
	if(mode == desiredMode && speed == oldSpeed){
		return true;
	}
	
	if(desiredMode == GPS_MODE_UNKNOWN){
		warnx("Cant switch to unknown mode.");
		return false;
	}

	if(mode == GPS_MODE_UNKNOWN){
		warnx("Cant switch from unknown mode.");
		return false;
	}

	if(
		speed != 4800 &&
		speed != 9600 &&
		speed != 19200 &&
		speed != 38400)
	{
		
		warnx("Only speeds 4800, 9600, 19200 and 38400 are supported.");
		return false;
	}

	printf("Switching mode to %s\n", desiredMode == GPS_MODE_NMEA ? "NMEA" : "SIRF");

	if(mode != desiredMode){
		if(mode == GPS_MODE_NMEA){
			nmea.send(&port, "PSRF100,%d,%d,8,1,0",
				(desiredMode == GPS_MODE_NMEA ? 1 : 0), speed);
		}else if(mode == GPS_MODE_SIRF){
			assert(desiredMode == GPS_MODE_NMEA);
			// build the message 129 in the buffer.
			// EPE message mentioned twice? This code is copied from 
			// GPSD source, so this probably should work.
			char buffer[] = {
				0x81, 0x02,
				0x01, 0x01,             /* GGA */
				0x00, 0x00,             /* suppress GLL */
				0x01, 0x01,             /* GSA */
				0x05, 0x01,             /* GSV */
				0x01, 0x01,             /* RMC */
				0x00, 0x00,             /* suppress VTG */
				0x00, 0x01,             /* suppress MSS */
				0x00, 0x01,             /* suppress EPE */
				0x00, 0x01,             /* suppress EPE */
				0x00, 0x01,             /* suppress ZDA */
				0x00, 0x00,             /* unused */
				0x00, 0x00,             /* speed */
			};
			buffer[24] = hi8(speed);
			buffer[25] = lo8(speed);
			
			sirf.send(&port, buffer, sizeof(buffer));
		}
	}

	sleep(2);

	if(speed != oldSpeed){
		port.close();
		port.open(port.getPort(), speed);
	}
	
	return check_mode() == desiredMode;
}

/**
 * Make the current mode permanent.
 * This means that the original mode will not be restored
 * in the restore_mode() method or destructor.
 */
void SIRFGPS::permanent_mode(){
	if(mode == GPS_MODE_UNKNOWN){
		return;
	}

	oldMode = mode;
	oldSpeed = port.getSpeed();
}

/**
 * Restore the mode saved with permanent_mode() or constructor.
 */
void SIRFGPS::restore_mode(){
	if(mode != oldMode || port.getSpeed() != oldSpeed){
		switch_mode(oldMode, oldSpeed);
	}
}

/**
 * Lower byte of a 16bit number.
 */
unsigned SIRFGPS::lo8(unsigned n){
	return n & 0xFF;
}

/**
 * Upper byte of a 16bit number.
 */
unsigned SIRFGPS::hi8(unsigned n){
	return (n << 8)	&& 0xFF;
}
