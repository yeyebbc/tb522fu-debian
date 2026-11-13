"""Exercise CI's actual DT guard with positive and rejected encoded layouts."""
from pathlib import Path
import importlib.util
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_kernel', ROOT/'scripts/build-kernel.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
UART = '/soc@0/geniqup@8c0000/serial@89c000'
DTS = r'''/dts-v1/;
/ {
 aliases { serial0 = "/soc@0/geniqup@8c0000/serial@89c000"; };
 soc@0 {
  tlmm: pinctrl@f100000 { gpio-controller; #gpio-cells = <2>; };
  geniqup@8c0000 {
   serial@89c000 {
    status = "okay";
    rts-gpios = <&tlmm 60 0>;
    rs485-rts-delay = <1 0>;
    linux,rs485-enabled-at-boot-time;
    rs485-rx-during-tx;
    keyboard {
     compatible = "lenovo,tb522fu-keyboard";
     vcc3-enable-gpios = <&tlmm 105 0>;
     vcc5-enable-gpios = <&tlmm 106 0>;
     ocp-enable-gpios = <&tlmm 110 0>;
     mode-gpios = <&tlmm 42 0>;
     detect-gpios = <&tlmm 43 1>;
     lid-gpios = <&tlmm 11 1>;
    };
   };
  };
 };
};
'''

class KeyboardWiringTests(unittest.TestCase):
    def test_direction_owner_timing_and_existing_input_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, good = root/'board.dts', root/'good.dtb'
            source.write_text(DTS)
            subprocess.run(['dtc','-q','-I','dts','-O','dtb','-o',str(good),str(source)],check=True)
            build.check_keyboard_wiring(good)
            for name, args in [
                ('wrong_gate', ['-t','i',UART,'rts-gpios','1','61','0']),
                ('no_setup_delay', ['-t','i',UART,'rs485-rts-delay','0','0']),
                ('duplicate_owner', ['-t','i',UART+'/keyboard','tx-enable-gpios','1','60','0']),
                ('wrong_input_polarity', ['-t','i',UART+'/keyboard','lid-gpios','1','11','0']),
                ('wrong_controller', ['-t','i',UART,'rts-gpios','999','60','0']),
            ]:
                with self.subTest(name=name):
                    candidate = root/(name+'.dtb')
                    shutil.copy2(good,candidate)
                    subprocess.run(['fdtput',*args[:2],str(candidate),*args[2:]],check=True)
                    with self.assertRaises(AssertionError):
                        build.check_keyboard_wiring(candidate)
            missing = root/'missing.dtb'
            shutil.copy2(good,missing)
            subprocess.run(['fdtput','-d',str(missing),UART,'linux,rs485-enabled-at-boot-time'],check=True)
            with self.assertRaises(AssertionError):
                build.check_keyboard_wiring(missing)

if __name__ == '__main__':
    unittest.main()
