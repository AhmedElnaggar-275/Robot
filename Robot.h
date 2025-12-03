#ifndef ROBOT_H
#define ROBOT_H
#define RIGHT_LEG 1
#define LEFT_LEG 2

/*******************setup functions*********************/

void leg1_setup(int pin);
void leg2_setup(int pin);
void ultrsnc_head_setup(int echo1 , int trig1);

/********************Operation functions*****************/
void robot_init();
float read_distance();
void leg_act(int leg , int servo_state);
void move_2_steps(int t_delayms);
void rotate_1_step(int leg , int t_delayms);

#endif