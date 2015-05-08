##PWM Shield Library for Intel Edson
##Ethan Head, 2015
import mraa, time, math

class PWMShield:
	# Registers/etc.
	__MODE1              = 0x00
	__MODE2              = 0x01
	__SUBADR1            = 0x02
	__SUBADR2            = 0x03
	__SUBADR3            = 0x04
	__PRESCALE           = 0xFE
	__LED0_ON_L          = 0x06
	__LED0_ON_H          = 0x07
	__LED0_OFF_L         = 0x08
	__LED0_OFF_H         = 0x09
	__ALL_LED_ON_L       = 0xFA
	__ALL_LED_ON_H       = 0xFB
	__ALL_LED_OFF_L      = 0xFC
	__ALL_LED_OFF_H      = 0xFD

	# Bits
	__RESTART            = 0x80
	__SLEEP              = 0x10
	__ALLCALL            = 0x01
	__INVRT              = 0x10
	__OUTDRV             = 0x04

	#Scaling Values
	frequencyScale = .895
	frequencyOffset = .325
	pulseWidthScalingValue = 1.113

	def __init__(self, i2cBus,debugging=False,i2cAddress=0x40):
		self.i2c = mraa.I2c(i2cBus)
		self.i2cAddress = i2cAddress
		self.debugging = debugging
		self.frequency = 50 							#Default Frequency: 50 Hz
		self.reset()
		self.i2c.writeReg(self.__MODE2, self.__OUTDRV)
		self.i2c.writeReg(self.__MODE1, self.__ALLCALL)
		time.sleep(0.005)                               # wait for oscillator

		self.i2c.address(self.i2cAddress)
		mode1 = self.i2c.readReg(self.__MODE1)
		mode1 = mode1 & ~self.__SLEEP   	            # wake up (reset sleep)
		self.i2c.address(self.i2cAddress)
		self.i2c.writeReg(self.__MODE1, mode1)
		time.sleep(0.005)                               # wait for oscillator
		self.setFrequency(self.frequency)


	def reset(self):
		on=0
		off=0
		self.i2c.address(self.i2cAddress)
		self.i2c.writeReg(self.__ALL_LED_ON_L, on & 0xFF)
		self.i2c.writeReg(self.__ALL_LED_ON_H, on >> 8)
		self.i2c.writeReg(self.__ALL_LED_OFF_L, off & 0xFF)
		self.i2c.writeReg(self.__ALL_LED_OFF_H, off >> 8)

	def setPeriod(self, periodUs):
		frequency = 1000000/periodUs
		self.setFrequency(frequency)

	def setFrequency(self,frequency):
		"Sets the PWM frequency"
		self.frequency = frequency*frequencyScale  + frequencyOffset

		prescaleval = 25000000.0    # 25MHz
		prescaleval /= 4096.0       # 12-bit
		prescaleval /= float(self.frequency)
		prescaleval -= 1.0
		prescale = math.floor(prescaleval + 0.5)

		self.i2c.address(self.i2cAddress)
		oldmode = self.i2c.readReg(self.__MODE1)
		newmode = (oldmode & 0x7F) | 0x10				# sleep
		self.i2c.writeReg(self.__MODE1, newmode)	# go to sleep
		self.i2c.writeReg(self.__PRESCALE, int(math.floor(prescale)))
		self.i2c.writeReg(self.__MODE1, oldmode)
		time.sleep(0.005)
		self.i2c.writeReg(self.__MODE1, oldmode | 0x80) 

	def setPulseWidthUs(self, channel, length):
		if(self.debugging):
			print('PWM Pulse Length: %i us' %length)
		length *= pulseWidthScalingValue
		dataOFF = (4096*length*self.frequency)/1000000
		dataOFF = int(dataOFF)
		self.setPWM(channel,0,dataOFF)

	def setPWM(self, channel, on, off):
		"Sets a single PWM channel"
		if(self.debugging):
			print('On: %i Off:%i Channel: %i\n' % (on,off,channel))
		channel = int(channel)

		off = int(off)
		on = int(on)
		self.i2c.address(self.i2cAddress)
		self.i2c.writeReg(self.__LED0_ON_L+4*channel, on & 0xFF)
		self.i2c.writeReg(self.__LED0_ON_H+4*channel, on >> 8)
		self.i2c.writeReg(self.__LED0_OFF_L+4*channel, off & 0xFF)
		self.i2c.writeReg(self.__LED0_OFF_H+4*channel, off >> 8)


	def setDutyCycle(self,channel,percent):
		self.setPulseWidthUs(channel,percent*10000/self.frequency)
