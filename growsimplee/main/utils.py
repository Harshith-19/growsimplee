from sklearn.mixture import GaussianMixture
import requests
from growsimplee.settings import GOOGLE_API_KEY

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
	baseurl = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={x1},{y1}&destinations={x2}%2C{y2}&key={GOOGLE_API_KEY}"
	res = requests.get(baseurl)
	data = res.json()
	print(data)
	distance = data['rows'][0]['elements'][0]['distance']['value']
	time = data['rows'][0]['elements'][0]['duration']['value']
	return distance, time