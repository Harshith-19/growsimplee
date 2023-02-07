import cv2
import numpy as np

def findLength(path, wP = 210, hP = 270):
    webcam = False
    scale = 3
    wP *= scale
    hP *= scale

    
    if webcam: 
        cap = cv2.VideoCapture(0)
        cap.set(10,160)
        cap.set(3,1920)
        cap.set(4,1080)
        success, img = cap.read()
        pass
    else: 
        img = cv2.imread(path)
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    imgContours, conts = getContours(img, minArea=50000, showCanny=False, draw = False)

    if len(conts) != 0:
        biggest = conts[0][2]

        imgWarp = warpImg(img, biggest, wP, hP)
        imgContours2, conts2 = getContours(imgWarp, minArea=2000, showCanny=False, draw = False, cThr=[65,65], blurKernel=(5,5))

        if len(conts2) != 0:
            for obj in conts2:
                cv2.polylines(imgContours2, [obj[2]],True,(0,255,0),2)
                nPoints = reorder(obj[2])
                nW = findDis(nPoints[0][0]/scale, nPoints[1][0]/scale)
                nH = findDis(nPoints[0][0]/scale, nPoints[2][0]/scale)
                # cv2.arrowedLine(imgContours2, (nPoints[0][0][0], nPoints[0][0][1]), (nPoints[1][0][0], nPoints[1][0][1]),
                #                 (255, 0, 255), 3, 8, 0, 0.05)
                # cv2.arrowedLine(imgContours2, (nPoints[0][0][0], nPoints[0][0][1]), (nPoints[2][0][0], nPoints[2][0][1]),
                #                 (255, 0, 255), 3, 8, 0, 0.05)
                # x, y, w, h = obj[3]
                # cv2.putText(imgContours2, '{}cm'.format(nW), (x + 30, y - 10), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8,
                #             (255, 0, 255), 2)
                # cv2.putText(imgContours2, '{}cm'.format(nH), (x - 20, y + h // 2), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8,
                #             (255, 0, 255), 2)
        # cv2.imshow("A4", imgContours2)


        # img = cv2.resize(img, (0,0), None, 0.5,0.5)
        # cv2.imshow("Original", img)
        # cv2.waitKey(1)
    return nW, nH

def getContours(img, cThr = [80,80], showCanny = False, minArea = 1000, draw = False, blurKernel = (15,15)):
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, blurKernel,10)
    # cv2.imshow("Blur", imgBlur)
    imgCanny = cv2.Canny(imgBlur, cThr[0], cThr[1])

    kernel = np.ones((5,5))
    imgDial = cv2.dilate(imgCanny, kernel, iterations=3)
    imgThre = cv2.erode(imgDial, kernel, iterations=2)

    if showCanny: 
        imgTemp = cv2.resize(imgThre, (0,0), None, 0.5,0.5)
        cv2.imshow('Canny', imgTemp)

    contours, hiearchy = cv2.findContours(imgThre, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    finalCountours = []
    for i in contours:
        area = cv2.contourArea(i)

        if area > minArea:
            peri = cv2.arcLength(i, True)
            approx = cv2.approxPolyDP(i, 0.02*peri, True)
            bbox = cv2.boundingRect(approx)
            # 4 for finding rectangle
            # print("len(approx) :", len(approx))
            finalCountours.append([len(approx), area, approx, bbox, i])
            
    
    finalCountours = sorted(finalCountours, key = lambda x:x[1], reverse=True)

    if draw:
        for con in finalCountours:
            cv2.drawContours(img, con[4], -1,(0,0,255),3)

    return img, finalCountours

def reorder(myPoints):
    # print(myPoints.shape)
    myPointsNew = np.zeros_like(myPoints)
    myPoints = myPoints.reshape((4,2))

    add = myPoints.sum(1)
    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] = myPoints[np.argmax(add)]

    diff = np.diff(myPoints, axis = 1)
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]

    return myPointsNew

def warpImg(img, points, w, h, pad = 20):
    # print(points)
    points = reorder(points)
    # print(points)

    pts1 = np.float32(points)
    pts2 = np.float32([[0,0],[w,0],[0,h],[w,h]])

    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgWarp = cv2.warpPerspective(img, matrix, (w,h))

    imgWarp = imgWarp[pad:imgWarp.shape[0] - pad, pad:imgWarp.shape[1] - pad]

    return imgWarp

def findDis(pts1, pts2):
    ans = ((pts2[0] - pts1[0])**2 +  (pts2[1] - pts1[1])**2)**0.5
    return round(ans/10, 2)

def getVolume(TopImgPath, SideImgPath):
    wT, hT = findLength(TopImgPath)
    wS, hS = findLength(SideImgPath, wP = 160, hP = 255)

    # print("wT :", wT)
    # print("hT :", hT)
    # print("wS :", wS)
    # print("hS :", hS)

    height = (hT + hS) / 2
    width = wT
    length = wS

    volumetric_weight = (height * width * length) / 5000
    
    return volumetric_weight