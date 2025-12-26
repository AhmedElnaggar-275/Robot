#include "Robot.h"

char current_cmd = 0;    // to hold the current command until another command is received
bool stopped = false;   // to track if the robot is currently stopped or moving

void setup()
{
  R_leg_setup(9);     // right leg pin 9
  L_leg_setup(10);    // left leg pin 10
  ultrsnc_head_setup(12 , 11);  // echo pin 12 , trig pin 11
  robot_stop();               // initialize robot to stopped state
  stopped = true;
  Serial.begin(115200);       // start serial communication at 115200 rate to receive commands from serial monitor
}
void loop() {         // loop function runs over and over again forever
 // --- Read command from Serial ---
  if (Serial.available() > 0)   // Check if data is available to read (not -1)
  {
      int in = Serial.read();    // Read the incoming byte
      char cmd = (char) in ;    // Convert the byte to a character
      
      if (cmd != current_cmd && (cmd == 'F' || cmd == 'L' || cmd == 'R' || cmd == 'S'))  // check for valid commands only , also the new command must be different from the current one
                                                                 // F -> move forward , L -> rotate left , R -> rotate right , S -> stop
      {
        if(!stopped)
        {
          robot_stop();    // stop the robot after receiving a new valid command
                           // if this is not done and for example the robot is moving forward and a rotate command is received
                           // the robot may move the two legs at the same time causing moving forward instead of rotation

          stopped = true;     // update stopped state
        }

        current_cmd = cmd;     // Store the valid command for switch-case execution
      }
  }

  // --- Obstacle detection ---
  float distance = read_distance();

  if (distance > 0 && distance <= 15)   // Obstacle detected within 15 cm
  {
    current_cmd = 'S';   // force STOP ->> because it writes on the current_cmd variable after it was read from Serial
  }

  // --- Execute ONE STEP per loop ---
  switch (current_cmd)
  {
    case 'F':      // current command is Move Forward
      move(500 , 250);      // move forward with 500 ms delay operating each servo and 250 ms delay stop between steps
      if(stopped == true)     // note that it doesn't execute this unless stopped = true (just for clarity)
      {
        stopped = false;        // update stopped state if not updated
      }
      break;

    case 'L':     // current command is Rotate Left
      rotate(RIGHT_LEG, 500 , 250);   // rotate left by moving right leg with 500 ms delay operating the servo and 250 ms delay stop
      if(stopped)
      {
        stopped = false;        // update stopped state if not updated
      }
      break;

    case 'R':     // current command is Rotate Right
      rotate(LEFT_LEG, 500 , 250);   // rotate right by moving left leg with 500 ms delay operating the servo and 250 ms delay stop
      if(stopped)
      {
        stopped = false;        // update stopped state if not updated
      }
      break;

    case 'S':     // current command is Stop
      if(!stopped)     // stop the robot only if it is not already stopped
      {
        robot_stop();
        stopped = true;
      }
      break;

    default:   // if Invalid command received due to any error - stop the robot if not already stopped
      if(!stopped)
      {
        robot_stop();
        stopped = true;
      }  
        break;
 }
}
