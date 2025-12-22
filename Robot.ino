#include "Robot.h"

int in = 0;      // for reading serial input as integer
char cmd = 0;    // to store the command as char
char currentCmd = 0;    // to hold the current command until another command is received
bool stopped = false;   // to track if the robot is currently stopped or moving

void setup()
{
  R_leg_setup(9);
  L_leg_setup(10);
  ultrsnc_head_setup(7 , 6);
  robot_stop();
  Serial.begin(115200);
}
void loop() {

  if (Serial.available() > 0)   // Check if data is available to read
  {
    in = Serial.read();     // Read as int to check for -1 (no data)
    if (in >= 0)                // Valid data read (not -1)
    {
      cmd = (char)in;      // Convert int to char (typecasting)
      if (cmd != '\n' && cmd != '\r')   // Ignore newline and carriage return characters (typical due to Enter key)
      {
        currentCmd = cmd;             // Store the valid command for switch-case execution
      }
    }
  }

  // --- Obstacle detection ---
  float distance = read_distance();

  if (distance > 0 && distance <= 10) 
  {
    // Obstacle detected within 10 cm
    currentCmd = 'S';   // force STOP ->> because it writes on the currentCmd variable after it was read from Serial
  }

  // --- Execute ONE STEP per loop ---
  switch (currentCmd) {

    case 'F':
      move_2_steps(500);
      stopped = false;
      break;

    case 'L':
      rotate_1_step(RIGHT_LEG, 500);
      stopped = false;
      break;

    case 'R':
      rotate_1_step(LEFT_LEG, 500);
      stopped = false;
      break;

    case 'S':
      if(!stopped){
      robot_stop();
      stopped = true;
      }
      break;

    default:   // if Invalid command - stop the robot
      currentCmd = 'S';
      break;
  }
}
