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

// serial monitor
Serial.begin(9600);

/***********************Setup Functions************************************************/

void R_leg_setup(int pin)         // right leg
{
    leg1.attach(pin);
    leg1_attached = true;
}

void L_leg_setup(int pin)         // left leg
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

    leg_act(RIGHT_LEG,STOP);
    leg_act(LEFT_LEG,STOP);

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
    duration = pulseIn(echo , HIGH);      // Echo pin is high until receiving the pulse again
    distance = (duration * 0.0343) / 2.0 ;       // distance calculation (cm)
    Serial.println(distance);
    return distance ;
}


void leg_act(int leg , int servo_state)    // 1 for right leg , 2 for left leg
{
    if (leg == RIGHT_LEG) 
    {
        leg1.write(servo_state);
    } 
    else if (leg == LEFT_LEG)
    {
        leg2.write(servo_state);
    }
}

void move_2_steps(unsigned int t_delayms)        // used inside a loop
{
    if (leg1_attached == false || leg2_attached == false)
    {
        Serial.println("Error: One or both legs are not attached.");
        return ;
    }
    
    robot_init();        // insuring stabiliy before moving

    leg_act(RIGHT_LEG , MOVE);
    delay(t_delayms);
    leg_act(RIGHT_LEG , STOP);
    delay(t_delayms);
    leg_act(LEFT_LEG , MOVE);
    delay(t_delayms);
    leg_act(LEFT_LEG , STOP);
    delay(t_delayms);
}
void rotate_1_step(int leg , unsigned int t_delayms)    // used inside a loop
{
    leg_act(leg , STOP);     // insuring stabiliy before moving
    if (leg == RIGHT_LEG)
    {
        leg_act(RIGHT_LEG , STOP);
    }
    else if (leg == LEFT_LEG)
    {
        leg_act(LEFT_LEG , STOP);
    }
    leg_act(leg , MOVE);
    delay(t_delayms);
    leg_act(leg , STOP);
}