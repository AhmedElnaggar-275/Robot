#ifndef ROBOT_H
#define ROBOT_H
#define RIGHT_LEG 1
#define LEFT_LEG 2
#define MOVE_R 0     // move right leg forward command
#define MOVE_L 180   // move left leg forward command
#define STOP  90     // stop specified leg command

enum WalkState {
  LEFT_STOP=0 , 
  RIGHT_MOVING , 
  RIGHT_STOP , 
  LEFT_MOVING} ; // finite state machine for move_2_steps function

enum RotateState {
  LEG_STOP=0 , 
  LEG_MOVING} ; // finite state machine for rotate_1_step function

/*******************setup functions*********************/

void R_leg_setup(int pin);
void L_leg_setup(int pin);
void ultrsnc_head_setup(int echo1 , int trig1);

/********************Operation functions*****************/
void robot_stop();             // robot initialization
float read_distance();   // ultrasonic distance reading
                         // returns distance in cm , returns -1 if no obstacle detected within range (approximately 40 cm)
void leg_act(int leg , int servo_action);     // leg = RIGHT_LEG or LEFT_LEG
                                             // servo_action = MOVE or STOP

void move_2_steps(unsigned int t_motion_delayms , unsigned int t_stop_delayms);   /*- t_motion_delayms : how much time in milliseconds one servo should move
                                                        - t_stop_delayms : how much time in milliseconds to wait between steps
                                                        - moving 2 steps forward by moving both legs alternately
                                                        - it moves one step at a time and then used in loop to continue moving
                                                        - the delay is non-blocking so other code can run during the stop or motion states
                                                       */
void rotate_1_step(int leg , unsigned int t_motion_delayms , unsigned int t_stop_delayms); /*leg = RIGHT_LEG or LEFT_LEG
                                                        - t_motion_delayms : how much time in milliseconds the servo should move
                                                        - t_stop_delayms : how much time in milliseconds to wait between steps
                                                        - rotating by moving one leg at a time
                                                        - it moves one step at a time and then used in loop to continue rotating
                                                        - the delay is non-blocking so other code can run during the stop or motion states
                                                       */ 

#endif