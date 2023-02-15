from sklearn.mixture import GaussianMixture
import requests
from growsimplee.settings import GOOGLE_API_KEY
from .models import *
import json

def cluster(points, num):
	gmm = GaussianMixture(n_components=num)
	gmm.fit(points)
	labels = gmm.predict(points)
	pointList = [[] for i in range(num)]
	for i, item in enumerate(labels):
		pointList[item].append(points[i])
	print(pointList)
	return pointList

def euclid_dist(x1, y1, x2, y2):
	try:
		baseurl = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={x1},{y1}&destinations={x2}%2C{y2}&key={GOOGLE_API_KEY}"
		res = requests.get(baseurl)
		data = res.json()
		print(data)
		distance = data['rows'][0]['elements'][0]['distance']['value']
		time = data['rows'][0]['elements'][0]['duration']['value']
		return distance, time
	except:
		return 1000, 600

def driverListResponse():
	drivers = Driver.objects.all()
	DriverList = []
	jsondeco = json.decoder.JSONDecoder()
	for per in drivers:
		instance = {}
		instance['Driver'] = per.person
		instance['path'] = []
		try:
			path = jsondeco.decode(per.path)
		except:
			path = []
		try:
			currPoint = jsondeco.decode(per.currentVisitedPoint)
		except:
			currPoint = []
		reached = False
		for i in range(len(path)):
			instance1 = {}
			instance1['id'] = i
			instance1['productID'] = path[i][0]
			if currPoint == []:
				instance1['reached'] = False
			elif reached == True:
				instance1['reached'] = True
			elif currPoint == path[i][0]:
				reached = True
				instance1['reached'] = True
			else:
				instance1['reached'] = True
			if currPoint == path[i][0]:
				instance1['current'] = True
			else:
				instance1['current'] = False
			instance1['type'] = path[i][1]
			product = Product.objects.get(productID=path[i][0])
			if path[i][1] == 's':
				instance1['latitude'] = product.sourceLatitude
				instance1['longitude'] = product.sourceLongitude
			else:
				instance1['latitude'] = product.destinationLatitude
				instance1['longitude'] = product.destinationLongitude
			instance['path'].append(instance1)
		DriverList.append(instance)
	return DriverList

def driverResponse(person):
	driver = Driver.objects.get(person=person)
	jsondeco = json.decoder.JSONDecoder()
	instance = {}
	instance['Driver'] = driver.person
	instance['path'] = []
	try:
		path = jsondeco.decode(driver.path)
	except:
		path = []
	try:
		currPoint = jsondeco.decode(driver.currentVisitedPoint)
	except:
		currPoint = []
	reached = False
	for i in range(len(path)):
		instance1 = {}
		instance1['id'] = i
		instance1['productID'] = path[i][0]
		if currPoint == []:
			instance1['reached'] = False
		elif reached == True:
			instance1['reached'] = True
		elif currPoint == path[i][0]:
			reached = True
			instance1['reached'] = True
		else:
			instance1['reached'] = True
		if currPoint == path[i][0]:
			instance1['current'] = True
		else:
			instance1['current'] = False
		instance1['type'] = path[i][1]
		product = Product.objects.get(productID=path[i][0])
		if path[i][1] == 's':
			instance1['latitude'] = product.sourceLatitude
			instance1['longitude'] = product.sourceLongitude
		else:
			instance1['latitude'] = product.destinationLatitude
			instance1['longitude'] = product.destinationLongitude
		instance['path'].append(instance1)
	return instance