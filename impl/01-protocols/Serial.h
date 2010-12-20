#ifndef SERIAL_H
#define SERIAL_H

#include <stdio.h>

#include <termios.h>
#include <unistd.h>

/**
 * Serial command line, fixed to 8N1, on unix mashines.
 */
class Serial{
public:
	void open(const char *port, unsigned speed);
	void close();

	int readc();
	void write(const void *data, size_t length);

	const char *getPort(){
		return currentPort;
	}

	unsigned getSpeed(){
		return currentSpeed;
	}

	void drop_unread();
	void drop_unsent();
private:
	const char *currentPort;
	unsigned currentSpeed;

	int fd;
	termios oldTermios;

	FILE *log;

	static const unsigned LOG_LINE_WIDTH = 16;
	static const char *LOG_FILE;
	unsigned char logReadBuffer[LOG_LINE_WIDTH];
	unsigned logReadBufferFill;

	void dump_log_read_buffer();
	void write_log_lines(char direction, const unsigned char *line, size_t count);
	void write_log_line(char direction, const unsigned char *line, size_t count);
};

#endif
