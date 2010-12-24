#ifndef SIRFGPS_H
#define SIRFGPS_H

#include "NMEAMessage.h"
#include "Serial.h"
#include "SIRFMessage.h"

class SIRFGPS{
public:
	SIRFGPS(const char *device);

	enum GPSMode{
		GPS_MODE_UNKNOWN,
		GPS_MODE_NMEA,
		GPS_MODE_SIRF,
	};

	enum GPSMode check_mode();

	enum GPSMode get_mode(){
		return mode;
	}

	bool switch_mode(GPSMode desiredMode, unsigned speed);
	void permanent_mode();
	void restore_mode();

	void get_one();
private:
	static const unsigned possibleSpeeds[];


	unsigned lo8(unsigned n);
	unsigned hi8(unsigned n);

	Serial port;
	NMEAMessage nmea;
	SIRFMessage sirf;

	GPSMode mode;
};

#endif
