#include "Serial.h"

#include <ctype.h>
#include <stdlib.h>
#include <stdio.h>

#include <err.h>

#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>

const char *Serial::LOG_FILE = "/tmp/serial.log";

/**
 * Read a single character from the port.
 */
int Serial::readc(){
	unsigned char c = 0;
	ssize_t status = read(fd, &c, 1);
	if(status < 0){
		err(EXIT_FAILURE, "Read failed.");
	}else if(status != 1){
		errx(EXIT_FAILURE, "Read didn't return a character, now tell me what to do :-(");
	}

	logReadBuffer[logReadBufferFill] = c;
	++logReadBufferFill;
	if(logReadBufferFill >= LOG_LINE_WIDTH){
		dump_log_read_buffer();
	}

	return c;
}

/**
 * Write data to the port.
 */
void Serial::write(const void *data, size_t length){
	ssize_t status = ::write(fd, data, length);

	if(status < 0){
		err(EXIT_FAILURE, "Write failed.");
	}else if(status != (ssize_t)length){
		errx(EXIT_FAILURE, "Write didn't finish writing all the data.");
	}

	dump_log_read_buffer();
	write_log_lines('>', (const unsigned char *)data, length);

	tcdrain(fd);
}

/**
 * Open a serial port.
 */
void Serial::open(const char *port, unsigned speed){
	fd = ::open(port, O_RDWR | O_NOCTTY);
	if(fd == -1){
		err(EXIT_FAILURE, "Opening port failed.");
	}

	termios newTermios;
	
	tcgetattr(fd, &oldTermios);
	tcgetattr(fd, &newTermios);

	switch(speed){
	case 4800:
		cfsetispeed(&newTermios, B4800);
		break;
	case 9600:
		cfsetispeed(&newTermios, B9600);
		break;
	case 19200:
		cfsetispeed(&newTermios, B19200);
		break;
	case 38400:
		cfsetispeed(&newTermios, B38400);
		break;
	default:
		errx(EXIT_FAILURE, "Only speeds 4800, 9600, 19200 and 38400 are supported.");
	}
	
	// hard coded to 8N1
	newTermios.c_cflag &= ~CSIZE;
	newTermios.c_cflag |= CS8;
	newTermios.c_cflag &= ~PARENB;
	newTermios.c_cflag &= ~CSTOPB;

	// disable canonical mode
	newTermios.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);

	newTermios.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP
		|INLCR | IGNCR | ICRNL | IXON);
	newTermios.c_oflag &= ~OPOST;
	
	
	
	// blocking read, inter-character timer 2s
	newTermios.c_cc[VTIME] = 20;
	newTermios.c_cc[VMIN] = 0;

	tcflush(fd, TCIOFLUSH);
	
	if(tcsetattr(fd, TCSAFLUSH, &newTermios)){
		err(EXIT_FAILURE, "tcsetattr failed.");
	}

	currentPort = port;
	currentSpeed = speed;

	log = stdout;//fopen(LOG_FILE, "w");
	logReadBufferFill = 0;
}

/**
 * Close a serial port.
 */
void Serial::close(){
	dump_log_read_buffer();
	//fclose(log);
	
	tcdrain(fd);

	tcsetattr(fd, TCSANOW, &oldTermios);
	::close(fd);
}

/**
 * Dump the whole log read buffer into the log file.
 */
void Serial::dump_log_read_buffer(){
	if(logReadBufferFill == 0){
		return;
	}
	write_log_line('<', logReadBuffer, logReadBufferFill);
	logReadBufferFill = 0;
}

/**
 * Write (possibly) may lines into the log file.
 */
void Serial::write_log_lines(char direction, const unsigned char *line, size_t count){
	while(count > LOG_LINE_WIDTH){
		write_log_line(direction, line, LOG_LINE_WIDTH);
		line += LOG_LINE_WIDTH;
		count -= LOG_LINE_WIDTH;
	}

	if(count > 0){
		write_log_line(direction, line, count);
	}
}

/**
 * Write a single line into the log file.
 */
void Serial::write_log_line(char direction, const unsigned char *line, size_t count){
	if(direction == '<'){
		fprintf(log, "<  |");
	}else{
		fprintf(log, " > |");
	}

	for(unsigned i = 0; i < count; ++i){
		fprintf(log, " %02x", (int)(line[i]));
	}

	
	for(unsigned i = count; i < LOG_LINE_WIDTH; ++i){
		fprintf(log, "   ");
	}

	fprintf(log, " | ");

	for(unsigned i = 0; i < count; ++i){
		if(isgraph(line[i])){
			fputc(line[i], log);
		}else{
			fputc('.', log);
		}
	}

	fputc('\n', log);
}

/**
 * Remove all the characters that were received but not read from the buffer.
 */
void Serial::drop_unread(){
	dump_log_read_buffer();
	fprintf(log, "<  | Read buffer flushed.\n");
	tcflush(fd, TCIFLUSH);
}

/**
 * Remove all the characters that were received but not read from the buffer.
 */
void Serial::drop_unsent(){
	fprintf(log, " > | Write buffer flushed.\n");
	tcflush(fd, TCOFLUSH);
}
