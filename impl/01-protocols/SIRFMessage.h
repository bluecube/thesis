#ifndef SIRFMESSAGE_H
#define SIRFMESSAGE_H

#include "Serial.h"

class SIRFMessage{
public:
	SIRFMessage();
	~SIRFMessage();

	bool parse(Serial *s);

	void send(Serial *s, void *payload, size_t count);

	void *payload(){
		return buffer;
	}
	size_t payload_length(){
		return payloadLength;
	}
private:
	ssize_t findMessageBeginning(Serial *s);

	static const size_t MAX_PAYLOAD_LENGTH = 0x7FFF;
	static const size_t MAX_MESSAGE_LENGTH = MAX_PAYLOAD_LENGTH + 8;
	unsigned char *buffer;
	size_t payloadLength;
};

#endif
