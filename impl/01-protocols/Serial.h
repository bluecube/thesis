#ifndef SERIAL_H
#define SERIAL_H

#include <stdio.h>

#include <termios.h>
#include <unistd.h>

//#define SERIAL_DUMP_DATA

/**
 * Serial command line, fixed to 8N1, on unix mashines.
 */
class Serial{
public:
	void open(const char *port, unsigned speed);
	void close();

	int readc();
	void write(const void *data, size_t length);

	const char *get_port(){
		return currentPort;
	}

	unsigned get_speed(){
		return currentSpeed;
	}

	void drop_unread();
	void drop_unsent();

#ifdef SERIAL_DUMP_DATA
	void dump_log_read_buffer();
#else
	void dump_log_read_buffer(){}
#endif
private:
	const char *currentPort;
	unsigned currentSpeed;

	int fd;
	termios oldTermios;

#ifdef SERIAL_DUMP_DATA
	FILE *logFile;

	static const unsigned LOG_LINE_WIDTH = 16;
	static const char *LOG_FILE;
	unsigned char logReadBuffer[LOG_LINE_WIDTH];
	unsigned logReadBufferFill;

	void write_log_lines(char direction, const unsigned char *line, size_t count);
	void write_log_line(char direction, const unsigned char *line, size_t count);
#endif
};

#endif
