#include "SIRFGPS.h"

int main(){
	SIRFGPS gps("/dev/ttyUSB0", 4800);

	for(int i = 0; i < 100; ++i){
		gps.get_one();
	}

	gps.switch_mode(SIRFGPS::GPS_MODE_NMEA, 4800);
	gps.switch_back_on_exit(false);
}
