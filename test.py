import requests

#curl http://ec2-52-40-133-183.us-west-2.compute.amazonaws.com:1738/classify -d 'data={"youth":1}' -X POST

data='data={"youth":1}'
r = requests.post('http://ec2-52-40-133-183.us-west-2.compute.amazonaws.com:1738/classify', data=data)

print r.json()
