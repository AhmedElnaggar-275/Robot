#include "Robot.h"
#include <Arduino.h>
#include <Servo.h>

// ultrasonic head pins
int echo = 0 ;       // defined globally to be used in read_distance function easily without passing them as parameters
int trig = 0 ;

// servo objects
Servo leg1;
Servo leg2;


/***********************Setup Functions************************************************/

void R_leg_setup(int pin)         // right leg
{
    leg1.attach(pin);
}

void L_leg_setup(int pin)         // left leg
{
    leg2.attach(pin);
}

void ultrsnc_head_setup(int echo1 , int trig1)
{
    echo = echo1 ; trig = trig1 ;
    pinMode(echo , INPUT);
    pinMode(trig , OUTPUT);
}


/***********************Functions of operation*****************************************/ 

void robot_stop()                         // robot initialization
{

    leg_act(RIGHT_LEG, STOP);
    leg_act(LEFT_LEG, STOP);

}


float read_distance()
{
    float distance = 0 ;
    unsigned long duration = 0 ;
    digitalWrite(trig , LOW);             // Insuring that trig pin is LOW at the beginning
    delayMicroseconds(2);                   // trig off for 2 microseconds
    digitalWrite(trig , HIGH);
    delayMicroseconds(10);              
    /**triggering pulse for 10 microseconds
    to send the echo signal**/
    
    digitalWrite(trig , LOW);
    duration = pulseIn(echo, HIGH, 2332UL);
    // Echo pin is high until receiving the pulse again or after timeout of 2332 microseconds
    // in other words it can't read distance more than approximately 40 cm which is enough for our robot obstacle detection
    // this prevents getting stucked in pulseIn function if no obstacle is detected within range
    // maximum total time could be elapsed by this function is approximately 2.34 milliseconds
    
    if (duration == 0)
    {
        return -1 ;   // timeout occurred , no obstacle detected within range
    }
    distance = (duration * 0.0343) / 2.0 ;       // distance calculation (cm)

    return distance ;
}


void leg_act(int leg , int servo_action)      // leg action function instead of writing leg1.write or leg2.write every time
{
    if (leg == RIGHT_LEG) 
    {
        leg1.write(servo_action);
    } 
    else if (leg == LEFT_LEG)
    {
        leg2.write(servo_action);
    }
}

void move(unsigned int t_motion_delayms , unsigned int t_stop_delayms)        // used inside a loop
{   
    static WalkState state = LEFT_STOP ;   // static variable to hold the current state without reseting it on each function call
                                          // defining it every call won't take time but it is just best parctice for readability and debugging

    static unsigned long last_time = 0;   // static to hold its value without reseting it on each function call
    
    unsigned long now = millis();        //returns the time elapsed since the program started (milliseconds time)
                                         //it is a 32 bit number that overflows after approximately 49.71 days
                                         //overflow returns it to zero again

    if (state == LEFT_STOP || state == RIGHT_STOP)
    {
        if (now - last_time < t_stop_delayms){return ;}   // to control delay between steps instead of delay function
                                               //this allows other code to run during the waiting period of delay
                                               //So the function doesn't execute the next step until the specified delay time has passed
    }
    else
    {
        if (now - last_time < t_motion_delayms){return ;}   // to control delay between steps instead of delay function
                                               //this allows other code to run during the waiting period of delay
                                               //So the function doesn't execute the next step until the specified delay time has passed
    } 
    
    last_time = now ;           // to handle continuous increment of millis()
  
    switch (state)             // finite state machine
                              // finishes one state at each fucntion call and each function call is delayed by t_delayms after the previous one
                              // this is due to the delay control at the beginning of the function😉
    {
        case LEFT_STOP:                  // initial state or state after completing a full cycle
            leg_act(RIGHT_LEG , MOVE_R);
            state = RIGHT_MOVING ;       // state is RIGHT_MOVING until the next function call
            break;

        case RIGHT_MOVING:
            leg_act(RIGHT_LEG , STOP);
            state = RIGHT_STOP ;
            break;

        case RIGHT_STOP:
            leg_act(LEFT_LEG , MOVE_L);
            state = LEFT_MOVING ;
            break;

        case LEFT_MOVING:
            leg_act(LEFT_LEG , STOP);
            state = LEFT_STOP ;
            break;
    }
}
void rotate(int leg , unsigned int t_motion_delayms , unsigned int t_stop_delayms)    // used inside a loop
{
    static RotateState state = LEG_STOP ;   // static variable to hold the current state without reseting it on each function call
    static unsigned long last_time = 0;
    unsigned long now = millis();        //returns the time elapsed since the program started (milliseconds time)
                                        //it is a 32 bit number that overflows after approximately 49.71 days
                                        //overflow returns it to zero again
    if (state == LEG_STOP)
    {
        if (now - last_time < t_stop_delayms){return ;}   // to control delay between steps instead of delay function
                                               //this allows other code to run during the waiting period of delay
                                               //So the function doesn't execute the next step until the specified delay time has passed
    }
    else
    {
        if (now - last_time < t_motion_delayms){return ;}   // to control delay between steps instead of delay function
                                               //this allows other code to run during the waiting period of delay
                                               //So the function doesn't execute the next step until the specified delay time has passed
    }

    last_time = now ;           // to handle continuous increment of millis()
   
    switch (state)             // finite state machine
                              // finishes one state at each fucntion call and each function call is delayed by t_delayms after the previous one
                              // this is due to the delay control at the beginning of the function😉
    {
        case LEG_STOP:
            leg_act(leg ,(leg == RIGHT_LEG) ? MOVE_R : MOVE_L);   // ternary operator to choose the correct move macro based on the leg to be moved
            state = LEG_MOVING ;
            break;

        case LEG_MOVING:
            leg_act(leg , STOP);
            state = LEG_STOP ;
            break;
    }
}