#include <Wire.h>
#define MPU6050_ADDRESS 0x68
#define MPU_POWER_REG 0x6B
#define MPU_POWER_ON_COMMAND 0b00001000
#define GYRO_CONFIG_REG 0x1B
#define GYRO_CONFIG_VALUE 0b00001000
#define GYRO_CALIBRATION_QTY 2000
#define GYRO_SENSOR_DATA_REG 0x43
#define GYRO_SENSOR_DATA_QTY 6
#define MPU_SENSOR_TIMEOUT 2000
#define GYRO_FACTOR 65.536
#define TRIGGER A0
#define ECHO A1

float calibrated_gyro_value_x = 0, calibrated_gyro_value_y = 0, calibrated_gyro_value_z = 0;
float gyroscope_read_value;
unsigned long millis_time, micros_time;
float gyro_x, gyro_y, gyro_z;
int failCount = 0;
float totalAngleX = 0, totalAngleY = 0, totalAngleZ = 0;

void setupMPU()
{
  Wire.beginTransmission(MPU6050_ADDRESS);
  Wire.write(MPU_POWER_REG);
  Wire.write(MPU_POWER_ON_COMMAND);
  Wire.endTransmission();

  Wire.beginTransmission(MPU6050_ADDRESS);
  Wire.write(GYRO_CONFIG_REG);
  Wire.write(GYRO_CONFIG_VALUE);
  Wire.endTransmission();
}

void calibrateGyro()
{
  int i;

  micros_time = micros();
  for(i = 0; i < GYRO_CALIBRATION_QTY; ++i)
  {
    if(readGyroscope())
    {
      calibrated_gyro_value_x += gyro_x;
      calibrated_gyro_value_y += gyro_y;
      calibrated_gyro_value_z += gyro_z;

      while(micros() - micros_time < 4000);
      micros_time = micros();
    }
    else
    {
      --i;
      failCount++;
      if(failCount > 5)
      {
        return;
      }
    }
  }
  calibrated_gyro_value_x /= GYRO_CALIBRATION_QTY;
  calibrated_gyro_value_y /= GYRO_CALIBRATION_QTY;
  calibrated_gyro_value_z /= GYRO_CALIBRATION_QTY;
}

bool readGyroscope()
{
  Wire.beginTransmission(MPU6050_ADDRESS);
  Wire.write(GYRO_SENSOR_DATA_REG);
  Wire.endTransmission();
  Wire.requestFrom(MPU6050_ADDRESS, GYRO_SENSOR_DATA_QTY, true);
  millis_time = millis() + MPU_SENSOR_TIMEOUT;
  while(Wire.available() < GYRO_SENSOR_DATA_QTY && millis() < millis_time);
  if(millis() >= millis_time)
  {
    return false;
  }
  else
  {
    gyro_x = (Wire.read() << 8 | Wire.read()) / GYRO_FACTOR;
    gyro_y = (Wire.read() << 8 | Wire.read()) / GYRO_FACTOR;
    gyro_z = (Wire.read() << 8 | Wire.read()) / GYRO_FACTOR;
    return true;
  }
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(TRIGGER, OUTPUT);
  pinMode(ECHO, INPUT);
  Wire.begin();
  setupMPU();
  delay(30);
  calibrateGyro();
}

void loop() {
  // put your main code here, to run repeatedly:
  float changeInAngleX, changeInAngleY, changeInAngleZ;
  char input;
  long duration;
  float distance;
  micros_time = micros();
  if(readGyroscope())
  {
    changeInAngleX = (gyro_x - calibrated_gyro_value_x) * 0.065;
    changeInAngleY = (gyro_y - calibrated_gyro_value_y) * 0.065;
    changeInAngleZ = (gyro_z - calibrated_gyro_value_z) * 0.065;

    totalAngleX += changeInAngleX;
    totalAngleY += changeInAngleY;
    totalAngleZ += changeInAngleZ;
    digitalWrite(TRIGGER, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIGGER, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIGGER, LOW);
    delayMicroseconds(2);
    
    duration = pulseIn(ECHO, HIGH);
    distance = (duration * 0.0343) / 2;
    Serial.print(distance);
    Serial.print(',');
    Serial.println(totalAngleX, 0);
    while(micros() - micros_time < 65000);
  }
  else
  {
    if(failCount > 5)
    {
      while(true);
    }
    else
    {
      failCount++;
    }
  }
}
