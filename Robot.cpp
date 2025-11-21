#include "Robot.h"
#include <Arduino.h>
#include <Servo.h>

Servo leg1;
Servo leg2;
Serial.begin(9600);

/***********************Setup Functions************************************************/

void leg1_pin(short pin)         // right leg
{
    leg1.attach(pin);
}

void leg2_pin(short pin)         // left leg
{
    leg2.attach(pin);
}

void ultrsnc_head_pins(short echo , short trig)
{
    pinMode(echo , INPUT);
    pinMode(trig , OUTPUT);
}


/***********************Functions of operation*****************************************/ 

void robot_init()                         // robot initialization
{
    leg1_angle(0);
    leg2_angle(0);
}

void leg1_angle(short ang)         // right leg
{
    leg1.write(ang);
}

void leg2_angle(short ang)        // left leg
{
    leg2.write(ang); 
}


float ultrsnc_head(short echo , short trig)
{
    float distance = 0 ;
    unsigned short duration = 0 ;
    digitalWrite(trig , LOW);             // Insuring that trig pin is LOW at the beginning
    delayMicroseconds(2);                   // trig off for 2 microseconds
    digitalWrite(trig , HIGH);
    delayMicroseconds(10);              
    /**triggering pulse for 10 microseconds
    to send the echo signal**/
    digitalWrite(trig , LOW)
    duration = pulseIn(echo , HIGH);      // Echo pin is high until receiving the pulse again
    distance = (duration*.034321)/2 ;       // distance calculation
    Serial.println(distance);
    return distance ;
}

void move_2_steps()
{
    leg1_angle(90);
    delay(100);
    leg2_angle(0);
    delay(100);
    leg1_angle(0);
    delay(100);
    leg2_angle(90);
    delay(100);
}