#include "Robot.h"

int distance = 0 ;

void setup()
{
    R_leg_setup(9);        // right leg servo connected to pin 9
    L_leg_setup(10);       // left leg servo connected to pin 10
    ultrsnc_head_setup(7 , 6);   // ultrasonic sensor echo pin connected to pin 7 , trig pin connected to pin 6
    robot_init();
    Serial.begin(9600);
}

void loop()
{
     while(distance < 10)
    {
        distance = read_distance();
    }
    delay(2000);
    while(distance >= 10)   // rotation until an obstacle is detected (test only)
    {
        rotate_1_step(LEFT_LEG , 500);  // rotating to the left using right leg with delay of 500 milliseconds between steps
        distance = read_distance();
        Serial.println(distance);
        delay(100);
    }
    while(distance < 10)
    {
        distance = read_distance();
    }
    delay(2000);
    while(distance >= 10)   // move while distance is more than 10 cm
    {
        move_2_steps(500);   // moving the robot 2 steps with delay of 500 milliseconds between steps
        distance = read_distance();
        Serial.println(distance);
        delay(100);
    }
    
}