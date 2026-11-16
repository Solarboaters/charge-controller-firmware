# Copyright (c) The Libre Solar Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Compile the production function with hardware stand-ins. Requires g++."""
from pathlib import Path
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[2]

PREFIX = r'''
#include <cassert>
#define NUM_LEDS 3
#define LED_STATE_OFF 0
#define LED_STATE_ON 1
#define LED_STATE_BLINK 2
#define LED_STATE_FLICKER 3
int led_states[NUM_LEDS];
int trigger_timeout[NUM_LEDS];
bool blink_state=true;
'''

MAIN = r'''
int main(){
 for(int state=LED_STATE_ON;state<=LED_STATE_FLICKER;state++){
  for(int timeout=1;timeout<=5;timeout++){
   led_states[0]=state;trigger_timeout[0]=timeout;
   led_states[1]=state;trigger_timeout[1]=-1;
   led_states[2]=state;trigger_timeout[2]=0;
   bool blink=blink_state;
   for(int tick=1;tick<=timeout;tick++){
    leds_update_1s();
    assert(blink_state!=blink);blink=blink_state;
    assert(led_states[0]==(tick==timeout?LED_STATE_OFF:state));
    assert(led_states[1]==state);assert(trigger_timeout[1]==-1);
    assert(led_states[2]==LED_STATE_OFF);
   }
   leds_update_1s();assert(led_states[0]==LED_STATE_OFF);
  }
 }
}
'''

source = (REPO / "app/src/leds.cpp").read_text()
start = source.index("void leds_update_1s()")
end = source.index("\n}", start) + 2
with tempfile.TemporaryDirectory() as directory:
    source_file = Path(directory) / "test.cpp"
    executable = Path(directory) / "test"
    source_file.write_text(PREFIX + source[start:end] + MAIN)
    subprocess.run(["g++", "-std=c++17", str(source_file), "-o", str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
print("15 timed cases plus permanent, zero, subsequent-update and blink checks passed")
