#ifndef ROBOT_H
#define ROBOT_H
#define RIGHT_LEG 1
#define LEFT_LEG 2
#define MOVE_R 0      // move right leg forward
#define MOVE_L 180    // move left leg forward
#define STOP  90      // stop


enum WalkState {  // for finite state machine in move_2_steps function,
  LEFT_STOP = 0 ,
  RIGHT_MOVING,
  RIGHT_STOP,
  LEFT_MOVING
};

enum RotateState {  // for finite state machine in rotate_1_step function
  LEG_STOP = 0,
  LEG_MOVING
};


/*******************setup functions*********************/

void R_leg_setup(int pin);
void L_leg_setup(int pin);
void ultrsnc_head_setup(int echo1 , int trig1);

/********************Operation functions*****************/
void robot_stop();             // stops both legs or initializes the robot at the beginning
float read_distance();        // Ultrasonic distance reading

void leg_act(int leg , int servo_action);     // leg = RIGHT_LEG or LEFT_LEG
                                             // servo_action = MOVE , STOP or REV

void move_2_steps(unsigned int t_delayms);   /*- - moving the robot 2 steps
                                                 - t_delayms : 2*(delay between steps) in milliseconds 1/2*(t_delayms) for a step and 1/2*(t_delayms) for stopping
                                                 - used inside a loop to move the robot forward continuously
                                                  , avoid steps conflict and to standardize delay between steps
                                                 */

void rotate_1_step(int leg , unsigned int t_delayms); /*leg = RIGHT_LEG or LEFT_LEG to rotate left or right respectively
                                                        - t_delayms : 2*(delay between steps) in milliseconds 1/2*(t_delayms) for a step and 1/2*(t_delayms) for stopping
                                                        - rotating 1 step by moving one leg only
                                                        - used inside a loop to rotate the robot continuously
                                                       */ 

#endif