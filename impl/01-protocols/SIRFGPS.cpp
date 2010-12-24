#include "SIRFGPS.h"

#include <assert.h>
#include <err.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * Baud rates that we're working with.
 * These are tried at startup, 
 */
const unsigned SIRFGPS::possibleSpeeds[] = {4800, 9600, 19200, 38400};

/**
 * Open the serial port, autodetect port speed and GPS mode.
 */
SIRFGPS::SIRFGPS(const char *device){
	
	for(unsigned i = 0; i < (sizeof(possibleSpeeds) / sizeof(possibleSpeeds[0])); ++i){
		printf("Trying port speed %i.\n", possibleSpeeds[i]);
		port.open(device, possibleSpeeds[i]);
		if(check_mode() != GPS_MODE_UNKNOWN){
			printf("Valid setting found.\n");
			break;
		}
		port.close();
	}

	switch_mode(GPS_MODE_SIRF, 38400);
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
		port.dump_log_read_buffer();
		printf("GPS receiver is in NMEA 0183 mode.\n");
	}else if(sirf.parse(&port)){
		port.dump_log_read_buffer();
		printf("GPS receiver is in SIRF mode.\n");
		mode = GPS_MODE_SIRF;
	}else{
		port.dump_log_read_buffer();
		printf("GPS receiver is in unknown mode.\n");
		mode = GPS_MODE_UNKNOWN;
	}

	return mode;
}

void SIRFGPS::get_one(){
	if(mode == GPS_MODE_NMEA){
		warnx("We don't read NMEA messages.");
	}else if(mode == GPS_MODE_SIRF){
		if(!sirf.parse(&port)){
			warnx("Parsing of message failed.");
			return;
		}
		const char *payload = (const char *)sirf.payload();
		port.dump_log_read_buffer();
		printf("Received message %i (length: %i)\n", (int)(payload[0]), sirf.payload_length());
	}else{
		warnx("Cant read messages in unknown mode.");
		return;
	}
}


bool SIRFGPS::switch_mode(SIRFGPS::GPSMode desiredMode, unsigned speed){
	if(mode == desiredMode && speed == port.get_speed()){
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

	bool found = false;
	for(unsigned i = 0; i < (sizeof(possibleSpeeds) / sizeof(possibleSpeeds[0])); ++i){
		if(possibleSpeeds[i] == speed){
			found = true;
			break;
		}
	}

	if(!found){
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
				0x00, 0x01,             /* suppress ZDA */
				0x00, 0x00,             /* unused */
				0x00, 0x00,             /* speed */
			};
			buffer[22] = hi8(speed);
			buffer[23] = lo8(speed);
			
			sirf.send(&port, buffer, sizeof(buffer));
		}
	}

	// settle time
	sleep(2);

	if(speed != port.get_speed()){
		port.close();
		port.open(port.get_port(), speed);
	}
	
	return check_mode() == desiredMode;
}

void SIRFGPS::permanent_mode(){
	if(mode == GPS_MODE_UNKNOWN){
		return;
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
	return (n >> 8) & 0xFF;
}