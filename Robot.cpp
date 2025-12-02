#include "Robot.h"
#include <Arduino.h>
#include <Servo.h>

// ultrasonic head pins
int echo = 0 ;
int trig = 0 ;

// servos
Servo leg1;
Servo leg2;
bool leg1_attached = false;
bool leg2_attached = false;
const int move = 180 ;
const int stop = 90 ;
const int reverse = 0 ;

/***********************Setup Functions************************************************/

void leg1_setup(int pin)         // right leg
{
    leg1.attach(pin);
    leg1_attached = true;
}

void leg2_setup(int pin)         // left leg
{
    leg2.attach(pin);
    leg2_attached = true;
}

void ultrsnc_head_setup(int echo1 , int trig1)
{
    echo = echo1 ; trig = trig1 ;
    pinMode(echo , INPUT);
    pinMode(trig , OUTPUT);
}


/***********************Functions of operation*****************************************/ 

void robot_init()                         // robot initialization
{

    leg1_angle(stop);
    leg2_angle(stop);

}

void leg1_angle(int servo_state)         // right leg
{
    if (leg1_attached) leg1.write(servo_state);
    else Serial.println("Leg 1 not attached!");
}

void leg2_angle(int servo_state)        // left leg
{
    if (leg2_attached) leg2.write(servo_state); 
    else Serial.println("Leg 2 not attached!");
}


float ultrsnc_head()
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
    duration = pulseIn(echo , HIGH);      // Echo pin is high until receiving the pulse again
    distance = (duration * 0.034321) / 2.0 ;       // distance calculation (cm)
    Serial.println(distance);
    return distance ;
}


void leg_act(int leg , int servo_state)    // 1 for right leg , 2 for left leg
{
    if (leg == 1) 
    {
        leg1.write(servo_state);
    } 
    else if (leg == 2)
    {
        leg2.write(servo_state);
    }
}

void move_2_steps(int t_delayms)                   // used inside a loop
{
    leg_act(1 , stop);        // insuring stabiliy before moving
    leg_act(2 , stop);

    leg_act(1 , move);
    delay(t_delayms);
    leg_act(1 , stop);
    delay(t_delayms);
    leg_act(2 , move);
    delay(t_delayms);
    leg_act(2 , stop);
    delay(t_delayms);
}
void rotate_1_step(int leg , int t_delayms)    // used inside a loop
{
    leg_act(leg , stop);     // insuring stabiliy before moving

    leg_act(leg , move);
    delay(t_delayms);
    leg_act(leg , stop);
}