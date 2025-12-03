#ifndef ROBOT_H
#define ROBOT_H
#define RIGHT_LEG 1
#define LEFT_LEG 2
#define MOVE  180 
#define STOP  90
#define REV  0

/*******************setup functions*********************/

void R_leg_setup(int pin);
void L_leg_setup(int pin);
void ultrsnc_head_setup(int echo1 , int trig1);

/********************Operation functions*****************/
void robot_init();             // robot initialization
float read_distance();        // ultrasonic distance reading

void leg_act(int leg , int servo_state);     // leg = RIGHT_LEG or LEFT_LEG
                                             // servo_state = MOVE , STOP or REV

void move_2_steps(unsigned int t_delayms);   /*- t_delayms : delay between steps in milliseconds
                                               - moving the robot 2 step to be used in loop
                                                  inorder not to type leg.write(MOVE) and leg.write(STOP) more than once
                                                  , avoid steps conflict and to standardize delay between steps
                                                  **after each step the function read_distance() must be called separately to check for obstacles**
                                                 */

void rotate_1_step(int leg , unsigned int t_delayms); /*leg = RIGHT_LEG or LEFT_LEG
                                                        - t_delayms : delay between steps in milliseconds
                                                        - rotating 1 step by moving one leg
                                                        - it rotates one step at a time and then used in loop
                                                          where after each step the function read_distance is called to check for obstacles
                                                        - **the function read_distance is not automatically called inside this function**
                                                        - **distance_read() must be called separately after each step to check for obstacles**
                                                          
                                                       */ 

#endif