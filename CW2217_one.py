import smbus
import time
from datetime import datetime 
import subprocess

I2C_BUS = 1  
CW2217_ADDRESS = 0x64  
VCELL_HIGH_REG = 0x02  
VCELL_LOW_REG = 0x03  
SOC_HIGH_REG = 0x04  
SOC_LOW_REG = 0x05 
TEMP_REG = 0x06 
VERSION_REG = 0x00  
CONTROL_REG = 0x08  
CURRENT_MSB_REG = 0x0E
CURRENT_LSB_REG = 0x0F
R_SENSE = 10.0

def check_initialization(bus):
    try:
        control_val = bus.read_byte_data(CW2217_ADDRESS, CONTROL_REG)
        print(f"CONTROL_REG value: 0x{control_val:02X}")
        return control_val != 0x00
    except Exception as e:
        print(f"Error reading CONTROL_REG: {e}")
        return True

def initialize_cw2217(bus):
    try:
        bus.write_byte_data(CW2217_ADDRESS, CONTROL_REG, 0xF0)
        time.sleep(0.5)
        bus.write_byte_data(CW2217_ADDRESS, CONTROL_REG, 0x30)
        time.sleep(0.5)  
        bus.write_byte_data(CW2217_ADDRESS, CONTROL_REG, 0x00)
        time.sleep(0.5)  
        bus.write_byte_data(CW2217_ADDRESS, 0x0b, 0x80)
        time.sleep(0.5)  
        print("CW2217 initialized successfully")
    except Exception as e:
        print(f"Initialization failed: {e}")

def read_data(bus):
    try:
        vcell_high = bus.read_byte_data(CW2217_ADDRESS, VCELL_HIGH_REG)
        vcell_low = bus.read_byte_data(CW2217_ADDRESS, VCELL_LOW_REG)
        voltage = ((((vcell_high << 8) | vcell_low) & 0x3FFF) * 0.0003125)*3

        soc_high = bus.read_byte_data(CW2217_ADDRESS, SOC_HIGH_REG)
        soc_low = bus.read_byte_data(CW2217_ADDRESS, SOC_LOW_REG)
        soc_raw = soc_high + (soc_low / 256.0)
        soc = min(max(soc_raw, 0.0), 100.0)

        temp = bus.read_byte_data(CW2217_ADDRESS, TEMP_REG)
        temp_c = -40 + (temp / 2)

        current_msb = bus.read_byte_data(CW2217_ADDRESS, CURRENT_MSB_REG)
        current_lsb = bus.read_byte_data(CW2217_ADDRESS, CURRENT_LSB_REG)
        raw_current = int.from_bytes([current_msb, current_lsb], byteorder='big', signed=True)
        current = (52.4 * raw_current) / (32768 * R_SENSE)
        
        return voltage, soc, temp_c, current
        
    except Exception as e:
        print(f"Read failed: {e}")
        return None, None, None, None

def main():
    try:
        bus = smbus.SMBus(I2C_BUS)
        if check_initialization(bus):
            print("CW2217 requires initialization")
            power_script = "/home/user/Desktop/power.sh"
            print(f"Executing power script: {power_script}")
            try:
                subprocess.run(['bash', power_script], check=True)
                print("Power script executed successfully")
            except subprocess.CalledProcessError as e:
                print(f"Power script failed with error code: {e.returncode}")
            except FileNotFoundError:
                print(f"Script not found at {power_script}")
            except Exception as e:
                print(f"Error executing power script: {e}")
            initialize_cw2217(bus)
            time.sleep(3)  
        else:
            print("CW2217 already initialized, skipping initialization.")
        
        for i in range(3):
            voltage, soc, temp_c, current = read_data(bus)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            if voltage is not None:
                print(f"\n[Time: {timestamp}]")
                print(f"Voltage: {voltage:.3f} V")
                print(f"SOC: {soc:.2f}%")
                print(f"Temperature: {temp_c:.1f} C")
                print(f"Current: {current:.3f} A")
                print("-" * 20)
            else:
                print("Failed to read data")
                
            time.sleep(1)  
            
        print("\nCompleted 3 readings. Exiting...")
            
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        print("Program terminated")

if __name__ == "__main__":
    main()
