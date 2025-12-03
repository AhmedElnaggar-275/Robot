int distance = 0 ;
void setup()
{
    leg1_setup(9);        // right leg servo connected to pin 9
    leg2_setup(10);       // left leg servo connected to pin 10
    ultrsnc_head_setup(7 , 6);   // ultrasonic sensor echo pin connected to pin 7 , trig pin connected to pin 6
    robot_init();
}

void loop()
{
    distance = read_distance();
    while(distance > 5)   // rotation until an obstacle is detected (test only)
    {
        rotate_1_step(RIGHT_LEG , 500);  // rotating to the left using right leg with delay of 500 milliseconds between steps
        distance = read_distance();
    }
    while(distance > 5)   // move while distance is more than 5 cm
    {
        move_2_steps(500);   // moving the robot 2 steps with delay of 500 milliseconds between steps
        distance = read_distance();
    }
}