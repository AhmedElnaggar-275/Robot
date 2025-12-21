#include "Robot.h"

char currentCmd = 0;
bool stopped = false;

void setup()
{
  R_leg_setup(9);
  L_leg_setup(10);
  ultrsnc_head_setup(7 , 6);
  robot_init();
  Serial.begin(115200);
}
void loop() {

  if (Serial.available() > 0)   // Check if data is available to read
  {
    int in = Serial.read();     // Read as int to check for -1 (no data)
    if (in >= 0)                // Valid data read (not -1)
    {
      char cmd = (char)in;      // Convert int to char (typecasting)
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
      robot_init();
      stopped = true;
      }
      break;

    default:   // Invalid command - stop the robot
      currentCmd = 'S';
      break;
  }
}
