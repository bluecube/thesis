#ifndef NMEAMESSAGE_H
#define NMEAMESSAGE_H

#include "Serial.h"

/**
 * NMEA parser.
 */
class NMEAMessage{
public:
	bool parse(Serial *s);

	void send(Serial *s, const char *format, ...);

	const char *field(int n);
	size_t fieldLength(int n);

	const char *operator[](int n){
		return field(n);
	}

	/**
	 * Maximal length of NMEA data (between $ and *).
	 * I'm not really sure this limit really works, but
	 * I hope so.
	 */
	static const int MAX_MSG_LEN = 80;
private:
	int hexChar(int c);
	char buffer[MAX_MSG_LEN];
	
	/**
	 * Pointers to the terminating NULLs in the buffer.
	 */
	char *bufferIndexes[MAX_MSG_LEN + 6];
	int bufferIndexCount;
};

#endif
