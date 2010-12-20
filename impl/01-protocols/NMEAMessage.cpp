#include "NMEAMessage.h"

#include <err.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

const char *NMEAMessage::field(int n){
	if(n < 0 || n >= bufferIndexCount){
		return NULL;
	}else if(n == 0){
		return buffer;
	}else{
		return bufferIndexes[n - 1] + 1;
	}
}

size_t NMEAMessage::fieldLength(int n){
	if(n < 0 || n >= bufferIndexCount){
		return 0;
	}else if(n == 0){
		return bufferIndexes[0] - buffer;
	}else{
		return bufferIndexes[n] - bufferIndexes[n - 1] - 1;
	}
	
}

/**
 * Parse the message and also optionally determine whether
 * the serial line sends NMEA messages.
 *
 * \return true if the message found a valid NMEA message
 * reasonably soon, false otherwise.
 */
bool NMEAMessage::parse(Serial *s){

	bufferIndexCount = 0;
	int c = s->readc();
	int counter;

	// eat the possible garbage before message beginning
	counter = 1;
	c = s->readc();
	while(c != '$'){
		c = s->readc();
		++counter;
		if(counter > 2 * MAX_MSG_LEN){
			return false;
		}
	}
	
	int tmpIndexCount = 0;

	int checksum = 0;
	char *p = buffer;
	counter = 0;
	do{
		c = s->readc();
		++counter;
		if(counter > 2 * MAX_MSG_LEN){
			//warnx("Maybe MAX_MSG_LEN is too short?");
			return false;
		}

		checksum ^= c;

		if(c == ',' || c == '*'){
			*p = '\0';
			bufferIndexes[tmpIndexCount] = p;
			++tmpIndexCount;
		}else{
			*p = c;
		}
		++p;
	}while(c != '*');

	// the star shouldn't have been a part of the checksummed data, so remove it.
	checksum ^= '*';

	int expectedChecksum;
	expectedChecksum = 16 * hexChar(s->readc());
	expectedChecksum += hexChar(s->readc());

	if(checksum != expectedChecksum){
		return false;
	}

	c = s->readc();
	if(c == '\r'){
		c = s->readc();
	}
	if(c != '\n'){
		return false;
	}

	bufferIndexCount = tmpIndexCount;
	return true;
}

/**
 * Wrap a printf-like string into correct NMEA message header and footer
 * and send it to the given port.
 */
void NMEAMessage::send(Serial *s, const char *format, ...){
	va_list va;

	va_start(va, format);
	buffer[0] = '$';
	int count = vsnprintf(buffer + 1, MAX_MSG_LEN, format, va);
	va_end(va);

	if(count >= MAX_MSG_LEN){
		errx(EXIT_FAILURE, "Message would have been too long.");
	}

	unsigned checksum = 0;
	for(int i = 1; i <= count; ++i){
		checksum ^= buffer[i];
	}

	sprintf(buffer + count + 1, "*%02X\r\n", checksum);

	s->write(buffer, count + 6);
}

/**
 * Interpret the character as a hexadecimal digit.
 */
int NMEAMessage::hexChar(int c){
	if(c >= '0' && c <= '9')
		return c - '0';
	else if(c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	else if(c >= 'a' && c <= 'f')
		return c -'a' + 10;
	else return -1;

}
