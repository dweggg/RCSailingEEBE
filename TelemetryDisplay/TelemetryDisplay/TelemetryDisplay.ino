#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <math.h>

// -------- Display configuration --------
#define TFT_CS    D3  
#define TFT_RST   D2  
#define TFT_DC    D1  

Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

// -------- Sensor variables (0..5000) --------
float windDir = 0.0, batteryVolt = 0.0, extra1 = 0.0, extra2 = 0.0;
bool newDataAvailable = false;

// -------- IMU data variables --------
float roll = 0.0, pitch = 0.0, yaw = 0.0;
float acx = 0.0, acy = 0.0, acz = 0.0;
float gyx = 0.0, gyy = 0.0, gyz = 0.0;
float mgx = 0.0, mgy = 0.0, mgz = 0.0;
bool imuDataReady = false;

// -------- Bar display settings --------
#define MAX_SENSOR      5000.0       // Maximum sensor value
#define BAR_MAX_WIDTH   180          // Outer width of the bar (including border)
#define BAR_HEIGHT      20           // Outer height of the bar (including border)
#define BAR_SPACING     20           
#define BAR_X           10           // X coordinate for bars
#define INNER_OFFSET    1            // Border thickness

// Inner bar dimensions (area that changes)
#define INNER_WIDTH   (BAR_MAX_WIDTH - 2*INNER_OFFSET)
#define INNER_HEIGHT  (BAR_HEIGHT - 2*INNER_OFFSET)

// Bar Y positions for each sensor
#define BAR_Y1 40
#define BAR_Y2 (BAR_Y1 + BAR_HEIGHT + BAR_SPACING)
#define BAR_Y3 (BAR_Y2 + BAR_HEIGHT + BAR_SPACING)
#define BAR_Y4 (BAR_Y3 + BAR_HEIGHT + BAR_SPACING)

// Circle and line for wind direction
#define CIRCLE_RADIUS  40
#define CIRCLE_X       250
#define CIRCLE_Y       120
#define LINE_LENGTH    38

#define LINE_THICKNESS 3

// Previous inner widths for each sensor bar
int prevWidthDir = 0, prevWidthBat = 0, prevWidthEx1 = 0, prevWidthEx2 = 0;
int prevWindDir = -1;  // Keeps track of the previous wind direction for optimization

// -------- IMU Display settings --------
#define IMU1_MAX 180.0  // For ROL, PIT, YAW (orientation)
#define IMU2_MAX 10.0   // For Accelerometer (ACX, ACY, ACZ)
#define IMU3_MAX 250.0  // For Gyroscope (GYX, GYY, GYZ)
#define IMU4_MAX 100.0  // For Magnetometer (MGX, MGY, MGZ)
#define AXIS_MAX_LENGTH 30  // Maximum length in pixels for each axis line

// Define horizontal centers for the 4 IMU groups
int imuCenterX[4] = {40, 120, 200, 280};  
#define IMU_CENTER_Y 210  // Common Y position for all IMU groups

// Array to store previous endpoints for IMU axis lines: [group][axis][x,y]
int prevIMUEndpoint[4][3][2]; // 4 groups, 3 axes (X, Y, Z), 2 coordinates each

// Function prototypes
void drawStaticElements();
void updateBar(int x, int y, float sensorValue, uint16_t color, int &prevWidth);
void updateWindDirection(float dir);
void updateIMUGroup(uint8_t group, float xVal, float yVal, float zVal, float maxVal);

void drawStaticElements() {
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(ST77XX_WHITE);

  // Draw sensor labels (static)
  tft.setCursor(10, BAR_Y1 + (BAR_HEIGHT / 2) - 25 );
  tft.print("DIR");
  tft.setCursor(10, BAR_Y2 + (BAR_HEIGHT / 2) - 25 );
  tft.print("BAT");
  tft.setCursor(10, BAR_Y3 + (BAR_HEIGHT / 2) - 25 );
  tft.print("EX1");
  tft.setCursor(10, BAR_Y4 + (BAR_HEIGHT / 2) - 25 );
  tft.print("EX2");

  // Draw bar borders once for each sensor
  tft.drawRect(BAR_X, BAR_Y1, BAR_MAX_WIDTH, BAR_HEIGHT, ST77XX_WHITE);
  tft.drawRect(BAR_X, BAR_Y2, BAR_MAX_WIDTH, BAR_HEIGHT, ST77XX_WHITE);
  tft.drawRect(BAR_X, BAR_Y3, BAR_MAX_WIDTH, BAR_HEIGHT, ST77XX_WHITE);
  tft.drawRect(BAR_X, BAR_Y4, BAR_MAX_WIDTH, BAR_HEIGHT, ST77XX_WHITE);

  // Draw circle border (wind direction)
  tft.drawCircle(CIRCLE_X, CIRCLE_Y, CIRCLE_RADIUS, ST77XX_WHITE);

  // Draw labels for IMU groups
  tft.setTextSize(1);
  tft.setCursor(imuCenterX[0]-10, IMU_CENTER_Y + AXIS_MAX_LENGTH + 5);
  tft.print("ORI");
  tft.setCursor(imuCenterX[1]-10, IMU_CENTER_Y + AXIS_MAX_LENGTH + 5);
  tft.print("ACC");
  tft.setCursor(imuCenterX[2]-10, IMU_CENTER_Y + AXIS_MAX_LENGTH + 5);
  tft.print("GYR");
  tft.setCursor(imuCenterX[3]-10, IMU_CENTER_Y + AXIS_MAX_LENGTH + 5);
  tft.print("MAG");
}

void setup() {
  Serial.begin(115200);
  delay(100);

  tft.init(240, 320);
  tft.setRotation(1);
  tft.setSPISpeed(40000000);
  
  drawStaticElements();

  // Initialize previous endpoints for IMU axes to the center position
  for (int g = 0; g < 4; g++) {
    for (int a = 0; a < 3; a++) {
      prevIMUEndpoint[g][a][0] = imuCenterX[g];
      prevIMUEndpoint[g][a][1] = IMU_CENTER_Y;
    }
  }
}

void loop() {
  // Read incoming serial data
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("DIR:")) {
      windDir = line.substring(4).toFloat();
    }
    else if (line.startsWith("BAT:")) {
      batteryVolt = line.substring(4).toFloat();
    }
    else if (line.startsWith("EX1:")) {
      extra1 = line.substring(4).toFloat();
    }
    else if (line.startsWith("EX2:")) {
      extra2 = line.substring(4).toFloat();
      // When EX2 is received, we assume a complete ADC set is ready.
      newDataAvailable = true;
    }
    else if (line.startsWith("ROL:")) {
      roll = line.substring(4).toFloat();
    }
    else if (line.startsWith("PIT:")) {
      pitch = line.substring(4).toFloat();
    }
    else if (line.startsWith("YAW:")) {
      yaw = line.substring(4).toFloat();
    }
    else if (line.startsWith("ACX:")) {
      acx = line.substring(4).toFloat();
    }
    else if (line.startsWith("ACY:")) {
      acy = line.substring(4).toFloat();
    }
    else if (line.startsWith("ACZ:")) {
      acz = line.substring(4).toFloat();
    }
    else if (line.startsWith("GYX:")) {
      gyx = line.substring(4).toFloat();
    }
    else if (line.startsWith("GYY:")) {
      gyy = line.substring(4).toFloat();
    }
    else if (line.startsWith("GYZ:")) {
      gyz = line.substring(4).toFloat();
    }
    else if (line.startsWith("MGX:")) {
      mgx = line.substring(4).toFloat();
    }
    else if (line.startsWith("MGY:")) {
      mgy = line.substring(4).toFloat();
    }
    else if (line.startsWith("MGZ:")) {
      mgz = line.substring(4).toFloat();
      // When MGZ is received, we assume a complete IMU set is ready.
      imuDataReady = true;
    }
  }

  // Update display if new data is ready
  if (newDataAvailable || imuDataReady) {
    tft.startWrite(); // Begin grouped SPI transaction

    if (newDataAvailable) {
      updateBar(BAR_X, BAR_Y1, windDir, ST77XX_GREEN, prevWidthDir);
      updateBar(BAR_X, BAR_Y2, batteryVolt, ST77XX_BLUE, prevWidthBat);
      updateBar(BAR_X, BAR_Y3, extra1, ST77XX_RED, prevWidthEx1);
      updateBar(BAR_X, BAR_Y4, extra2, ST77XX_YELLOW, prevWidthEx2);
      updateWindDirection(windDir);
      newDataAvailable = false;
    }

    if (imuDataReady) {
      // Group 0: Orientation (ROL, PIT, YAW)
      updateIMUGroup(0, roll, pitch, yaw, IMU1_MAX);
      // Group 1: Accelerometer (ACX, ACY, ACZ)
      updateIMUGroup(1, acx, acy, acz, IMU2_MAX);
      // Group 2: Gyroscope (GYX, GYY, GYZ)
      updateIMUGroup(2, gyx, gyy, gyz, IMU3_MAX);
      // Group 3: Magnetometer (MGX, MGY, MGZ)
      updateIMUGroup(3, mgx, mgy, mgz, IMU4_MAX);
      imuDataReady = false;
    }

    tft.endWrite();   // End grouped SPI transaction
  }
}


// Updates only the changed portion of a bar for a given sensor
void updateBar(int x, int y, float sensorValue, uint16_t color, int &prevWidth) {
  // Map sensor value (0 to MAX_SENSOR) to inner width (0 to INNER_WIDTH)
  if(sensorValue < 0) sensorValue = 0;
  if(sensorValue > MAX_SENSOR) sensorValue = MAX_SENSOR;
  int newWidth = (int)((sensorValue / MAX_SENSOR) * INNER_WIDTH);

  // If the bar has grown, fill the new section with the sensor color
  if(newWidth > prevWidth) {
    tft.fillRect(x + INNER_OFFSET + prevWidth, y + INNER_OFFSET,
                 newWidth - prevWidth, INNER_HEIGHT, color);
  }
  // If the bar has shrunk, clear the extra section by filling with black
  else if(newWidth < prevWidth) {
    tft.fillRect(x + INNER_OFFSET + newWidth, y + INNER_OFFSET,
                 prevWidth - newWidth, INNER_HEIGHT, ST77XX_BLACK);
  }
  // Update the previous width for the next update
  prevWidth = newWidth;
}

// Update the wind direction circle
void updateWindDirection(float dir) {
  int newAngle = map(dir, 0, MAX_SENSOR, 0, 360); // Convert sensor value to 0..360 degrees
  
  if (newAngle != prevWindDir) {
    int prevXEnd = CIRCLE_X + LINE_LENGTH * cos(radians(prevWindDir));
    int prevYEnd = CIRCLE_Y - LINE_LENGTH * sin(radians(prevWindDir));

    // Clear previous line using thick line drawing with black color
    drawThickLine(CIRCLE_X, CIRCLE_Y, prevXEnd, prevYEnd, ST77XX_BLACK, LINE_THICKNESS);

    int newXEnd = CIRCLE_X + LINE_LENGTH * cos(radians(newAngle));
    int newYEnd = CIRCLE_Y - LINE_LENGTH * sin(radians(newAngle));

    // Draw new red line with desired thickness
    drawThickLine(CIRCLE_X, CIRCLE_Y, newXEnd, newYEnd, ST77XX_RED, LINE_THICKNESS);

    prevWindDir = newAngle;
  }
}

// Update a specific IMU group with new values for its three axes
void updateIMUGroup(uint8_t group, float xVal, float yVal, float zVal, float maxVal) {
  const int baseAngles[3] = {0, 120, 240};
  const uint16_t axisColors[3] = {ST77XX_RED, ST77XX_GREEN, ST77XX_BLUE};
  int centerX = imuCenterX[group];
  int centerY = IMU_CENTER_Y;
  
  float values[3] = {xVal, yVal, zVal};
  
  for (int i = 0; i < 3; i++) {
    float val = values[i];
    float absVal = fabs(val);
    float scale = absVal / maxVal;
    if(scale > 1.0) scale = 1.0;
    int len = (int)(scale * AXIS_MAX_LENGTH);
    int angle = baseAngles[i];
    if(val < 0) {
      angle = (angle + 180) % 360;
    }
    int newX = centerX + len * cos(radians(angle));
    int newY = centerY - len * sin(radians(angle));
    
    if(newX != prevIMUEndpoint[group][i][0] || newY != prevIMUEndpoint[group][i][1]) {
      // Clear previous thick line
      drawThickLine(centerX, centerY, prevIMUEndpoint[group][i][0],
                    prevIMUEndpoint[group][i][1], ST77XX_BLACK, LINE_THICKNESS);
      // Draw new thick line
      drawThickLine(centerX, centerY, newX, newY, axisColors[i], LINE_THICKNESS);
      
      prevIMUEndpoint[group][i][0] = newX;
      prevIMUEndpoint[group][i][1] = newY;
    }
  }
}


// Helper function to draw a thick line
void drawThickLine(int x0, int y0, int x1, int y1, uint16_t color, uint8_t thickness) {
  if (thickness <= 1) {
    tft.drawLine(x0, y0, x1, y1, color);
    return;
  }
  // Calculate line vector components
  float dx = x1 - x0;
  float dy = y1 - y0;
  float len = sqrt(dx * dx + dy * dy);
  // Avoid division by zero
  if (len == 0) {
    tft.drawPixel(x0, y0, color);
    return;
  }
  // Perpendicular vector (normalized)
  float px = -dy / len;
  float py = dx / len;
  
  int half = thickness / 2;
  for (int offset = -half; offset <= half; offset++) {
    int x0_off = x0 + round(px * offset);
    int y0_off = y0 + round(py * offset);
    int x1_off = x1 + round(px * offset);
    int y1_off = y1 + round(py * offset);
    tft.drawLine(x0_off, y0_off, x1_off, y1_off, color);
  }
}
