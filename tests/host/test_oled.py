# Copyright (c) The Libre Solar Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Compile the production function with hardware stand-ins. Requires g++."""
from pathlib import Path
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[2]

PREFIX = r'''
#include <cmath>
#include <cstdio>
#include <string>
#include <cassert>
using std::abs;
struct Bus { float voltage=12; } bus;
struct PowerPort { Bus *bus; float power,neg_energy_Wh; };
PowerPort solar_terminal{&bus,-123,456},grid_terminal{&bus,-789,999},bat_terminal{&bus,0,0};
struct { int state=0; float power=0,current=0,pos_energy_Wh=0; } load;
#define LOAD_STATE_ON 1
struct { int soc=50; bool ext_temp_sensor=false; float bat_temperature=25; } charger;
struct { float solar_in_total_Wh=0,load_out_total_Wh=0,internal_temp=25; } dev_stat;
unsigned char bmp_load[1],bmp_pv_panel[1],bmp_disconnected[1],bmp_arrow_right[1];
bool half_bridge_enabled() {return true;}
float half_bridge_get_duty_cycle() {return 0.5;}
struct Display {
 std::string text;
 void clear() {text.clear();}
 template<class... A> void drawBitmap(A...) {}
 template<class... A> void drawRect(A...) {}
 template<class... A> void setTextCursor(A...) {}
 void writeString(char *s,unsigned n) {text.append(s,n);}
 void display() {}
} oled;
'''

source = (REPO / "app/src/oled.cpp").read_text()
function = source[source.index("void oled_update()"):source.index("void oled_thread()")]
CASES = [
    ("LV solar / HV battery", ["LV_TERMINAL_SOLAR", "HV_TERMINAL_BATTERY"], "123W"),
    ("LV solar / HV grid", ["LV_TERMINAL_SOLAR", "HV_TERMINAL_NANOGRID"], "123W"),
    ("HV solar", ["HV_TERMINAL_SOLAR"], "123W"),
    ("HV grid", ["HV_TERMINAL_NANOGRID"], "789W"),
    ("PWM solar", ["PWM_TERMINAL_SOLAR"], "123W"),
]
with tempfile.TemporaryDirectory() as directory:
    for name, definitions, expected in CASES:
        source_file = Path(directory) / "test.cpp"
        executable = Path(directory) / "test"
        main = '\nint main() { oled_update(); assert(oled.text.find("' + expected + '") != std::string::npos); }\n'
        source_file.write_text(PREFIX + function + main)
        subprocess.run([
            "g++", "-std=c++17", *["-DCONFIG_" + key + "=1" for key in definitions],
            str(source_file), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable)], check=True)
        print(name + ": passed")
