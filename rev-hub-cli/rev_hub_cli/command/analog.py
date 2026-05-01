"""Analog input and current/voltage measurement commands."""

from rev_core.expansion_hub import ExpansionHub


async def analog(hub: ExpansionHub, channel: int, continuous: bool) -> None:
    while True:
        value = await hub.get_analog_input(channel)
        print(f"ADC: {value} mV")
        if not continuous:
            break


async def temperature(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        value = await hub.get_temperature()
        print(f"Temperature: {value} C")
        if not continuous:
            break


async def battery_voltage(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        value = await hub.get_battery_voltage()
        print(f"Battery Voltage: {value} mV")
        if not continuous:
            break


async def battery_current(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        value = await hub.get_battery_current()
        print(f"Battery Current: {value} mA")
        if not continuous:
            break


async def voltage_rail(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        value = await hub.get_5v_bus_voltage()
        print(f"5V rail: {value} mV")
        if not continuous:
            break


async def i2c_current(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        value = await hub.get_i2c_current()
        print(f"I2C Current: {value} mA")
        if not continuous:
            break


async def servo_current(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        value = await hub.get_servo_current()
        print(f"Servo Current: {value} mA")
        if not continuous:
            break


async def motor_current(hub: ExpansionHub, channel: int, continuous: bool) -> None:
    while True:
        value = await hub.get_motor_current(channel)
        print(f"Motor {channel} Current: {value} mA")
        if not continuous:
            break


async def digital_bus_current(hub: ExpansionHub, continuous: bool) -> None:
    while True:
        value = await hub.get_digital_bus_current()
        print(f"Digital Bus Current: {value} mA")
        if not continuous:
            break
