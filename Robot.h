#ifndef ROBOT_H
#define ROBOT_H

/*******************setup functions*********************/

void leg1_setup(short pin);
void leg2_setup(short pin);
void ultrsnc_head_setup(short echoin , short trigout);

/********************Operation functions*****************/
void robot_init();
void leg1_angle(short ang);
void leg2_angle(short ang);
float ultrsnc_head(short echo , short trig);
void move_2_steps();

#endif