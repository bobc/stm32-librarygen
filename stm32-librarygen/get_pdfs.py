import urllib
import urllib2
from urllib2 import Request, urlopen
from urllib import FancyURLopener
import os

class MyOpener(FancyURLopener, object):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'


def get_file2 (url, dest_path):
    myopener = MyOpener();

    # req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
    # req = urllib2.Request(url)

    # data = myopener.open(url)

    try:
        myopener.retrieve (url, dest_path)
        return 200
    except:
        return 0

    #print data.getcode()
    #print data.geturl()

    f = open (dest_path, "wb")
    f.write (data.read())
    f.close()

    return data.getcode(), data.geturl()


for ds in open ("datasheets.txt"):

    ds = ds.strip ()
    if ds:
        name = "pdf/" + os.path.split (ds)[-1]
        if not os.path.exists (name):
            print "getting %s, %s" % (ds, name)

            result = get_file2 (ds, name)
            if result != 200:
                print "%s %s" % (result, ds)
                print ("invalid datasheet URL")
