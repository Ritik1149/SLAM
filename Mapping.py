import cv2
import numpy
import serial
import time
import math
import threading
import sys

image = numpy.zeros((700, 1220, 3), dtype = numpy.uint8)
count = 1
mapGenerated = {}
listOfBoundaries= []
listOfWhites = []
inputReceived = False
phase1 = False
loopBreak = False
closeAll = False

# Lines 9 to 50 create an empty occupancy grid map and fill up all the cell addresses
for i in range(0, 700, 20):
    for j in range(0, 1220, 20):
        coordinateList = []
        if i == 680 or j == 1200:
            if i != 680:
                cv2.rectangle(image, (j, i), (j + 19, i + 20), (128, 128, 128), -1)
                for k in range(i, i + 21):
                    for l in range(j, j + 20):
                        coordinateList.append((l, k))
                mapGenerated[count] = coordinateList
            elif j != 1200:
                cv2.rectangle(image, (j, i), (j + 20, i + 19), (128, 128, 128), -1)
                for k in range(i, i + 20):
                    for l in range(j, j + 21):
                        coordinateList.append((l, k))
                mapGenerated[count] = coordinateList
            else:
                cv2.rectangle(image, (j, i), (j + 19, i + 19), (128, 128, 128), -1)
                for k in range(i, i + 20):
                    for l in range(j, j + 20):
                        coordinateList.append((l, k))
                mapGenerated[count] = coordinateList
        else:
            cv2.rectangle(image, (j, i), (j + 20, i + 20), (128, 128, 128), -1)
            for k in range(i, i + 21):
                for l in range(j, j + 21):
                    coordinateList.append((l, k))
            mapGenerated[count] = coordinateList
        count += 1

coordinateList = [] # Resetting here, because it is used again in the main loop
for i in range(0, 701, 20):
    if i == 700:
        cv2.line(image, (0, i - 1), (1219, i - 1), (255, 255, 255), 1)
    else:
        cv2.line(image, (0, i), (1219, i), (255, 255, 255), 1)
    for j in range(0, 1221, 20):
        if i == 0:
            if j == 1220:
                cv2.line(image, (j - 1, 0), (j - 1, 699), (255, 255, 255), 1)
            else:
                cv2.line(image, (j, 0), (j, 699), (255, 255, 255), 1)
        else:
            pass

# Setting up Ourselves
cv2.circle(image, (610, 350), 10, (0, 0, 255), -1)

# Defining a patli gali way out while not stopping the main loop
def listenForStop():
    global inputReceived
    global closeAll
    while True:
        command = input("Press ENTER to stop the current process:")
        if command.lower() == 'exit':
            closeAll = True
        inputReceived = True

threading.Thread(target = listenForStop, daemon = True).start()

# Establishing a serial communication with Arduino UNO from line 59 to line 68
serialObject = serial.Serial('COM6', baudrate = 9600, timeout = 20)

while True:
    if closeAll:
        print("\nTerminating the program")
        serialObject.close()
        sys.exit(0)
    copyImage = image.copy()
    # getting stuff from Arduino UNO
    serialObject.reset_input_buffer()
    line = serialObject.readline().decode('utf-8')
    if ',' in line:
        distanceInString, angleInString = line.split(',')
    if len(angleInString) > 1:
        angleInInt = int(angleInString, base = 10)
    if len(distanceInString) > 1:
        distanceInFloat = float(distanceInString)
    angleInRadians = math.radians(-angleInInt) # math module methods take angle in radians
    rotationMatrix = numpy.array([[math.cos(angleInRadians), -math.sin(angleInRadians)], [math.sin(angleInRadians), math.cos(angleInRadians)]])
    # rendering our heading direction
    resultOfRotation = rotationMatrix.dot(numpy.array([[0], [-20]]))
    newAngleCoordinatesOfUs = numpy.array([[resultOfRotation[0][0] + 610], [resultOfRotation[1][0] + 350]])
    cv2.line(copyImage, (610, 350), (round(newAngleCoordinatesOfUs[0][0]), round(newAngleCoordinatesOfUs[1][0])), (0, 160, 255), 3)

    if not phase1 and not inputReceived:
        if distanceInFloat > 20:
            pass
        else:
            possibleDistance = distanceInFloat / 3
            distanceInPixels = round(possibleDistance * 56)
            obstacleCoordinates = (610, 350 - distanceInPixels)
            resultOfRotation = rotationMatrix.dot(numpy.array([[obstacleCoordinates[0] - 610], [obstacleCoordinates[1] - 350]]))
            newAngleCoordinatesOfObstacle = (round(resultOfRotation[0][0] + 610), round(resultOfRotation[1][0] + 350))
            for i in range(1, count):
                for j in range(len(mapGenerated[i])):
                    if mapGenerated[i][j][0] == newAngleCoordinatesOfObstacle[0] and mapGenerated[i][j][1] == newAngleCoordinatesOfObstacle[1]:
                        cv2.rectangle(image, mapGenerated[i][0], mapGenerated[i][-1], (0, 0, 0), -1)
                        if i not in listOfBoundaries:
                            listOfBoundaries.append(i)
                        loopBreak = True
                        break
                if loopBreak:
                    loopBreak = False
                    break
            print(listOfBoundaries)
            '''newAngleCoordinatesOfObstacleSimplified = ((newAngleCoordinatesOfObstacle[0] // 20) * 20, (newAngleCoordinatesOfObstacle[1] // 20) * 20)
            cv2.rectangle(image, (newAngleCoordinatesOfObstacleSimplified[0] + 1, newAngleCoordinatesOfObstacleSimplified[1] + 1), (newAngleCoordinatesOfObstacleSimplified[0] + 19, newAngleCoordinatesOfObstacleSimplified[1] + 19), (0, 0, 0), -1)'''
            for i in range(20, distanceInPixels):
                coordinates = (610, 350 - i)
                resultOfRotation = rotationMatrix.dot(numpy.array([[coordinates[0] - 610], [coordinates[1] - 350]]))
                newAngleCoordinatesOfWhite = (round(resultOfRotation[0][0] + 610), round(resultOfRotation[1][0] + 350))
                newAngleCoordinatesOfWhite = ((newAngleCoordinatesOfWhite[0] // 20) * 20, (newAngleCoordinatesOfWhite[1] // 20) * 20)
                for j in range(1, count):
                    if mapGenerated[j][0] == newAngleCoordinatesOfWhite and newAngleCoordinatesOfWhite not in listOfWhites and newAngleCoordinatesOfWhite not in listOfBoundaries:
                        listOfWhites.append(newAngleCoordinatesOfWhite)
                        cv2.rectangle(image, (newAngleCoordinatesOfWhite[0], newAngleCoordinatesOfWhite[1]), (newAngleCoordinatesOfWhite[0] + 20, newAngleCoordinatesOfWhite[1] + 20), (255, 255, 255), -1)
                        break
                        
        cv2.imshow("Map", copyImage)
        cv2.waitKey(10)