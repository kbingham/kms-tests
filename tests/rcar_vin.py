#!/usr/bin/python3

import os
import glob

# model strings are null terminated:
rcar_gen3_models = [
    'Renesas Salvator-X board based on r8a7795 ES1.x\0',
    'Renesas Salvator-X 2nd version board based on r8a7795 ES2.0+\0',
    'Renesas Salvator-X board based on r8a7796\0',
    'Renesas Eagle board based on r8a77970\0',
]

rcar_gen3_vin = [
    'e6ef0000',
    'e6ef1000',
    'e6ef2000',
    'e6ef3000',
    'e6ef4000',
    'e6ef5000',
    'e6ef6000',
    'e6ef7000',
]

rcar_gen3_csi2 = [
    'fea80000',
    'fea90000',
    'feaa0000',
    'feab0000',
]


class MediaController(object):
    def __init__(self, device):
        for f in glob.glob("/dev/media*"):
            print(f)
        self.cmd = "/usr/bin/media-ctl -d " + device + " "

    def reset(self):
        os.system(self.cmd + "-r")


class ADV748x(object):
    entities = ['afe', 'hdmi', 'txa', 'txb']

    def __init__(self, i2c_addr):
        self.basename = "adv748x " + i2c_addr

    def entity_name(self, entity):
        return self.basename + " " + entity


class RCar_VIN_G3(object):
    def __init__(self):
        self.model = open('/proc/device-tree/model', 'r').read()
        if self.model not in rcar_gen3_models:
            raise ValueError('Not a supported R-Car Gen3 platform: ' + self.model)

    # Perhaps we need an interface or python bindings for media controller
    def mc_get_mdev(self):
        for f in glob.glob("/dev/media*"):
            print(f)

    def vin_v4l2_device(self, idx):
        ''' Return the V4L2 device path (such as /dev/video23) for a given VIN '''
        path = "/sys/devices/platform/soc/" + rcar_gen3_vin[idx] + ".video/video4linux/video*"
        path = glob.glob(path)[0]
        return "/dev/" + os.path.basename(path)

    def vin_name(self, idx):
        return "rcar_vin " + rcar_gen3_vin[idx] + ".video"

    def csi2_name(self, idx):
        return "rcar_csi2 " + rcar_gen3_csi2[idx] + ".csi2"

    def hdmi_in(self):
        print("Configure for HDMI input")


#######################################################################################################################
# Selftesting

def selftest_MediaController():
    mc = MediaController("/dev/media0")
    mc.reset()


def selftest_RCar_VIN_G3():
    target = RCar_VIN_G3()
    print("Detected: " + target.model)
    print("Identifying VIN devices:")
    for i in range(8):
        print("    vin" + str(i) + ": " + target.vin_v4l2_device(i))
    target.mc_get_mdev()
    target.hdmi_in()


def selftest_ADV748x():
    adv = ADV748x("4-0070")
    print("ADV748x Entities:")
    for e in adv.entities:
        print("    " + e + ": " + adv.entity_name(e))

if __name__ == "__main__":
    selftest_MediaController()
    selftest_ADV748x()
    selftest_RCar_VIN_G3()
