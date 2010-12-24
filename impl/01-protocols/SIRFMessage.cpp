#include "SIRFMessage.h"

#include <err.h>
#include <stdlib.h>
#include <string.h>

SIRFMessage::SIRFMessage(){
	buffer = new unsigned char[MAX_MESSAGE_LENGTH];
}

SIRFMessage::~SIRFMessage(){
	delete[] buffer;
}

/**
 * Parse the message and also optionally determine whether
 * the serial line sends SIRF protocol messages.
 *
 * \return true if the message found a valid SIRF message
 * reasonably soon, false otherwise.
 */
bool SIRFMessage::parse(Serial *s){
	ssize_t status = findMessageBeginning(s);

	if(status < 0){
		return false;
	}

	payloadLength = status;

	unsigned checksum = 0;
	for(int i = 0; i < status; ++i){
		int c = s->readc();
		checksum += c;
		buffer[i] = c;
	}

	checksum &= 0x7FFF;

	unsigned expectedChecksum;
	expectedChecksum = s->readc() << 8;
	expectedChecksum |= s->readc();

	if(expectedChecksum != checksum){
		return false;
	}

	if(s->readc() != 0xB0){
		return false;
	}
	if(s->readc() != 0xB3){
		return false;
	}

	return true;
}

/**
 * Eat the possible garbage before message beginning.
 * \return length of the payload if the message beginning has been found.
 * -1 if too many characters passed and nothing that looks like message
 * has appeaared.
 * \bug The message header might alias with some data within the message
 * (if the message contains for example 0xA0 0xA2 0x00 0x10).
 * This means that theoretically we could never find out that the 
 * protocol is SIRF, or even worse read invalid data and not notice.
 * I don't know how to fix this.
 */
ssize_t SIRFMessage::findMessageBeginning(Serial *s){
	int state = 0;
	unsigned counter;
	ssize_t ret;

	// states:
	// 	0 - nothing
	// 	1 - got 0xA0
	// 	2 - got valid start sequence
	// 	3 - got valid start sequence and high byte of the payload length.
	// 		this terminates the search loop.

	counter = 0;
	while(true){
		int c = s->readc();
		++counter;
		if(counter > 2 * MAX_MESSAGE_LENGTH){
			return -1;
		}
		
		if(c == 0xA0){
			state = 1;
		}else if(c == 0xA2 && state == 1){
			state = 2;
		}else if(state == 2 && c <= 0x7F){
			ret = c << 8;
			break;
		}else{
			state = 0;
		}
	}

	ret |= s->readc();

	return ret;
}

void SIRFMessage::send(Serial *s, void *payload, size_t count){

	unsigned char *b = (unsigned char *)payload;

	if(count > MAX_PAYLOAD_LENGTH){
		errx(EXIT_FAILURE, "Payload too long.");
	}

	unsigned checksum = 0;
	for(unsigned i = 0; i < count; ++i){
		checksum += b[i];
	}

	checksum &= 0x7FFF;

	memcpy(buffer + 4, payload, count);

	buffer[0] = 0xA0;
	buffer[1] = 0xA2;
	buffer[2] = (count >> 8) & 0xFF;
	buffer[3] = count & 0xFF;


	buffer[count + 4] = (checksum >> 8) & 0xFF;
	buffer[count + 5] = checksum & 0xFF;
	buffer[count + 6] = 0xB0;
	buffer[count + 7] = 0xB3;

	s->write(buffer, count + 8);
}

