import cv2
import os
import fnmatch
import datetime
import sys
import time
import subprocess
from munkres import Munkres, print_matrix
import numpy as np

#function to retrive line parameters

def lineFromPoints(x1, y1, x2, y2):
    a = y2 - y1
    b = x1 - x2
    c = a*x1 + b*y1
    return (a, b, c)

#function to find specific file in a directory

def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

#function to decrease focus in subsequent iterations
    
def switchFocus(counter):
    return {
        48: 10,
        72: 15,
        96: 20,
        120: 25,
        148: 30,
        
    }.get(counter,counter)


#function that compute cost matrix and implements hungarian matching algorithm
  
def munkresCount(lines, counter, focus):
  myMatrix = []
  hoursCicle = 24
  alignThreshold = 30
  if counter > hoursCicle:
    spot = counter % hoursCicle
    if spot == 0:
      spot = hoursCicle
  else:
    spot = 0
  string = "lines{}_*".format(spot)
  path = os.path.join('linesFound')
  result = find(string, path)
  if result:
    print(result[0])
    for x in range(0, len(lines)):
      lineFound = False
      for x1, y1, x2, y2 in lines[x]:
        mylist = []
        with open(os.path.join(result[0]), mode = 'r+') as f:
          counter2 = 0
          line = f.readline()
          
          while line :
            counter2 += 1
            accumulator = 0
            parameter = line.split()
            first = parameter[0].replace(',', '')
            second = parameter[1].replace(',', '')        
            if int(first) == 0:
              
              accumulator += abs(int(first) - int(x1))
            
            else:
              accumulator += abs(((int(x1) - int(first))/int(first))* 100)
            if int(second) == 0:
              accumulator += abs(int(second) - int(y1))
            
            else:
              accumulator += abs(((int(y1) - int(second))/int(second))* 100)
            if int(parameter[2]) == 0:
              
              accumulator += abs(int(parameter[2]) - int(x2))
            else:
              accumulator += abs(((int(x2) - int(parameter[2]))/int(parameter[2]))* 100)
            mylist.append(int(accumulator))
            line = f.readline()
            
          myMatrix.append(mylist)
          
    print(myMatrix)      
    m = Munkres()
    alignment = 0
    indexes = m.compute(myMatrix)
    print(indexes)
    for row, column in indexes:
      value = myMatrix[row][column]
      
      if value < alignThreshold:
        
        alignment += 1
    resultString = "result{}_{}".format(counter, now.strftime("%Y-%m-%d_%H-%M-%S"))   
    jaccardIndex = alignment / (counter + len(lines) - alignment)
    f = open(os.path.join('results', 'results1'), "a")
    f.write("\n{} vs {}, align:{} , {} , {}  INDEX :{} with focus: {}\n".format(resultString, result[0], alignment, counter2, len(lines), jaccardIndex, focus  ))
    f.close()
    print(alignment, counter2 , len(lines))  
    print(jaccardIndex)
    return jaccardIndex
    
  else:
    pass     
  return 0



    
#main loop    

counter = 1
startTime = time.time()
timestep = 3600.0
focus = 0
#cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)
vc.set(3,1920)
vc.set(4,1080)
time.sleep(2)
vc.set(cv2.CAP_PROP_AUTOFOCUS, 0)
vc.set(cv2.CAP_PROP_FOCUS, focus)
dirname1 = 'imgCaptured'
dirname2 = 'linesFound'
dirname3 = 'imglines'
ramp_frames = 30


while True:
  
  window = 5
  jaccardVector = []
  
  while window > 0:
    
    time.sleep(5)
    focus = switchFocus(counter)
                              
    print ("capture n.",counter)
    if vc.isOpened(): # try to get the first frame
      
        for i in range(ramp_frames):
          temp = vc.read()
        rval, frame = vc.read()
    else:
      
        vc.open(0)
        vc.set(3,1920)
        vc.set(4,1080)
        time.sleep(2)
        vc.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        vc.set(cv2.CAP_PROP_FOCUS, focus)
        for i in range(ramp_frames):
            temp = vc.read()
        rval, frame = vc.read()
    if rval == True:
         
      #cv2.imshow("preview", frame)
      now = datetime.datetime.now()
      string = "frame{}_{}.jpg".format(counter, now.strftime("%Y-%m-%d_%H-%M-%S"))
      
      cv2.imwrite(os.path.join(dirname1, string), frame)
      #cv2.waitKey(0)
      vc.release()
      #cv2.destroyWindow("preview")
      string = "frame{}_{}gray.jpg".format(counter, now.strftime("%Y-%m-%d_%H-%M-%S"))
      img = frame
      img = cv2.resize(img, (1107, 623))
      gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
      cv2.imwrite(os.path.join(dirname1, string), gray)
      #cv2.imshow('Original image', img)
      #cv2.imshow('Gray image', gray)
      #cv2.waitKey(0)
      #cv2.destroyAllWindows()
      v = np.median(gray)
      lower = int(max(0, (1.0 - 0.33) * v))
      upper = int(min(255, (1.0 + 0.33) * v))
      string = "frame{}_{}edge.jpg".format(counter, now.strftime("%Y-%m-%d_%H-%M-%S"))
      edges = cv2.Canny(gray, lower, upper, None, 3)
      cv2.imwrite(os.path.join(dirname1, string), edges)
      #cv2.imshow('Edges', edges)
      #cv2.waitKey(0)
      #cv2.destroyAllWindows()
      
      #HoughLines probabilistic
      
      minLineLengthVal = 75
      maxLineGapVal = 10
      thresholdVal = 100
      lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=thresholdVal, minLineLength=minLineLengthVal, maxLineGap=maxLineGapVal)
      lstring = "lines{}_{}.txt".format(counter, now.strftime("%Y-%m-%d_%H-%M-%S") )
      f = open(os.path.join(dirname2, lstring), "w+")
      
      if lines is not None:
        
        for x in range(0, len(lines)):
          
            for x1, y1, x2, y2 in lines[x]:
              
                a, b, c = lineFromPoints(x1, y1, x2, y2)
                lines[x] = (a, b, c, 0)
                cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        linesSorted = sorted(lines, key = lambda x: x[0][0], reverse = True)
        jaccardIndex = munkresCount(linesSorted, counter, focus)
        
        for y in range (0, len(linesSorted)):
          
            for x1, y1, x2, y2 in linesSorted[y]:
              
                f.write("{}, {}, {} \n".format(x1, y1, x2))
                
      f.close()
      #cv2.imshow('Houghlines', img)
      #cv2.waitKey(0)
      #cv2.destroyAllWindows()
      ilstring = "img{}_{}.jpg".format(counter, now.strftime("%Y-%m-%d_%H-%M-%S"))
      cv2.imwrite(os.path.join(dirname3, ilstring), img)
      jaccardVector.append(jaccardIndex)
      window -= 1
    
  vc.release()
  print(np.median(jaccardVector))
  time.sleep(timestep - ((time.time() - startTime) %timestep))
  counter += 1



