

# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later


def preload_modules():
    from .wheels import wheels
    wheels.load_wheels_global_together(

        ["pyside6"]

    )