#!/usr/bin/python3

import kmstest


v4l2_warning = """
buildroot login: [ 1192.247238] ------------[ cut here ]------------
[ 1192.253245] WARNING: CPU: 1 PID: 4059 at /home/linuxembedded/iob/fdp1/kbuild-rcar/sources/linux/drivers/media/v4l2-core/videobuf2-core.c:1458 vb2_start_streaming+0xd4/0x150
[ 1192.271226] Modules linked in:
[ 1192.275575]
[ 1192.278328] CPU: 1 PID: 4059 Comm: yavta Tainted: G        W       4.7.0-rc3-00001-g9f21437be9ed-dirty #523
[ 1192.289384] Hardware name: Renesas Salvator-X board based on r8a7795 (DT)
[ 1192.297496] task: ffffffc02eba0000 ti: ffffffc02f3d8000 task.ti: ffffffc02f3d8000
[ 1192.306323] PC is at vb2_start_streaming+0xd4/0x150
[ 1192.312548] LR is at vb2_start_streaming+0x64/0x150
[ 1192.318763] pc : [<ffffff800866e8ec>] lr : [<ffffff800866e87c>] pstate: 60000145
[ 1192.327507] sp : ffffffc02f3dbb10
[ 1192.332149] x29: ffffffc02f3dbb10 x28: ffffffc02fb58780
[ 1192.338801] x27: ffffffc0317d6500 x26: 0000000000000001
[ 1192.345444] x25: ffffffc02f3dbd40 x24: 0000000000000000
[ 1192.352068] x23: 000000000000000a x22: 00000000fffffff4
[ 1192.358684] x21: ffffffc031d935f8 x20: ffffffc031d93780
[ 1192.365294] x19: ffffffc031d935d8 x18: 0000000000000001
[ 1192.371905] x17: 0000007f94cde3f0 x16: ffffff80081d5450
[ 1192.378506] x15: 003b9aca00000000 x14: 000000c8000000c8
[ 1192.385102] x13: 000000c8000000c8 x12: 000000c8000000c8
[ 1192.391675] x11: 000000c8000000c8 x10: 000000c8000000c8
[ 1192.398232] x9 : 0000000000000200 x8 : 0000000000000001
[ 1192.404778] x7 : 0000000000084084 x6 : ffffffc02f666108
[ 1192.411322] x5 : 0000000000000000 x4 : 0000000000000000
[ 1192.417858] x3 : 0000000000000000 x2 : 0000000000000001
[ 1192.424376] x1 : 0000000000000000 x0 : 0000000000000004
[ 1192.430861]
[ 1192.433481] ---[ end trace fab78d8be5167327 ]---
[ 1192.439239] Call trace:
[ 1192.442817] Exception stack(0xffffffc02f3db950 to 0xffffffc02f3dba70)
[ 1192.450420] b940:                                   ffffffc031d935d8 ffffffc031d93780
[ 1192.459430] b960: ffffffc02f3dbb10 ffffff800866e8ec ffffffbf00b69c80 ffffffbf00b69c80
[ 1192.468446] b980: ffffffc03100ed80 0000000000000000 ffffffc02f3db9b0 ffffff8008184c8c
[ 1192.477449] b9a0: 0000007f93fe0000 0000000108184b70 ffffffc02f3dba90 ffffff800809492c
[ 1192.486468] b9c0: ffffffc02eba0000 ffffffc02f3dbba0 ffffffc03100ed80 0000007f93fe000f
[ 1192.495477] b9e0: 0000000096000047 0000000000000015 0000000000000004 0000000000000000
[ 1192.504484] ba00: 0000000000000001 0000000000000000 0000000000000000 0000000000000000
[ 1192.513477] ba20: ffffffc02f666108 0000000000084084 0000000000000001 0000000000000200
[ 1192.522448] ba40: 000000c8000000c8 000000c8000000c8 000000c8000000c8 000000c8000000c8
[ 1192.531407] ba60: 000000c8000000c8 003b9aca00000000
[ 1192.537388] [<ffffff800866e8ec>] vb2_start_streaming+0xd4/0x150
[ 1192.544415] [<ffffff800867073c>] vb2_core_streamon+0x16c/0x1a0
[ 1192.551330] [<ffffff8008672eb4>] vb2_streamon+0x3c/0x60
[ 1192.557647] [<ffffff8008697d74>] vsp1_video_streamon+0x164/0x250
[ 1192.564753] [<ffffff8008657e60>] v4l_streamon+0x20/0x28
[ 1192.571077] [<ffffff800865bc0c>] __video_do_ioctl+0x25c/0x2c8
[ 1192.577907] [<ffffff800865b7d4>] video_usercopy+0x28c/0x448
[ 1192.584538] [<ffffff800865b9a4>] video_ioctl2+0x14/0x20
[ 1192.590781] [<ffffff8008656b20>] v4l2_ioctl+0xe8/0x118
[ 1192.596902] [<ffffff80081d4dac>] do_vfs_ioctl+0xa4/0x748
[ 1192.603187] [<ffffff80081d54dc>] SyS_ioctl+0x8c/0xa0
[ 1192.609136] [<ffffff8008084ecc>] __sys_trace_return+0x0/0x4
"""


zynqpanic = """
Kernel panic - not syncing: zynqmp_plat_init power management API version error. Expected: v0.3 - Found: v0.2

CPU: 0 PID: 1 Comm: swapper/0 Not tainted 4.9.0-00012-g98d93a7db7a0-dirty #2
Hardware name: ZynqMP ZCU102 RevB (DT)
Call trace:
[<ffffff8008087908>] dump_backtrace+0x0/0x1a0
[<ffffff8008087abc>] show_stack+0x14/0x20
[<ffffff80083d1c88>] dump_stack+0x94/0xb4
[<ffffff800812a384>] panic+0x114/0x25c
[<ffffff8008b4fa28>] zynqmp_plat_init+0x148/0x170
[<ffffff80080828b8>] do_one_initcall+0x38/0x128
[<ffffff8008b30be4>] kernel_init_freeable+0x84/0x1e0
[<ffffff800888bd18>] kernel_init+0x10/0x100
[<ffffff8008082680>] ret_from_fork+0x10/0x50
---[ end Kernel panic - not syncing: zynqmp_plat_init power management API version error. Expected: v0.3 - Found: v0.2
"""


def printk(msg):
    with open('/dev/kmsg', 'a') as log_buffer:
        log_buffer.write("<0>" + msg)


class FakeWarningLog(kmstest.KMSTest):
    """Generate a fake Kernel WARN_ON as part of a test."""

    def main(self):
        self.start("log validator recognition of a warning")

        for line in v4l2_warning.splitlines():
            printk(line)

        self.success()

FakeWarningLog().execute()


class FakePanicLog(kmstest.KMSTest):
    """Generate a fake Kernel Panic as part of a test."""

    def main(self):
        self.start("log validator recognition of a panic")

        for line in zynqpanic.splitlines():
            printk(line)

        self.success()

FakePanicLog().execute()
