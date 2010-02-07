import sys
sys.path.append("..")
import goove
import os
from xml.dom.minidom import parse, parseString

x = parse("pbsnodes.xml")

for i in x.childNodes[0].childNodes:
	name=i.getElementsByTagName("name")[0].childNodes[0].nodeValue
	np=i.getElementsByTagName("np")[0].childNodes[0].nodeValue
	properties=i.getElementsByTagName("properties")[0].childNodes[0].nodeValue
	print "name: ", name
	print "np: ", np
	print "properties: ", properties
