# -*- coding: cp936 -*-
import urllib
import urllib2
import os
import sys
import random
import threading

from bs4 import BeautifulSoup

class ZNGirls:

    def __init__(self,id):
        self.GirlID=str(id)
        self.GirlName=''
        self.GirlPage='https://www.nvshens.com/girl/' + self.GirlID + '/'
        self.GirlDesc=''
        self.GirlInfo=[]
        self.GirlAlbums=[]
        self.GirlSocial=[]
        self.GirlBWH=''
        self.GirlStore=''
        
    def getGirlName(self,soup):
        self.GirlName = soup.find("div", class_="div_h1").h1.string
        
    def getGirlPage(self):
        return self.GirlPage

    def getGirlDesc(self,soup):
        self.GirlDesc = soup.find("div", class_="infocontent").find("p").string

    def getGirlAlbums(self,soup):
        archives = soup.find_all("span",class_="archive_more")
        is_allAlbums = len(archives) <= 0
        if(is_allAlbums == False):
            archive_url = self.GirlPage + 'album/'
            html = self.get(archive_url)
            soup=BeautifulSoup(html,"html.parser")
        
        for album in soup.find_all("a", class_="igalleryli_link"):
            self.GirlAlbums.append('https://www.nvshens.com' + str(album["href"]))

    def getGirlStore(self,soup):
        self.GirlStore = soup.find("span", class_="score").contents[0]

    def getGirlAlbumName(self,soup):
        return soup.find("div", class_="albumTitle").h1.string
    
    def get(self,url):
        request=urllib2.Request(url)
        response=urllib2.urlopen(request)
        content=response.read().decode('utf-8')
        return content
    
    def getAlbumPagesCount(self,soup):
        pages=soup.find_all("div",id='pages')[0].find_all("a");
        count=len(pages)
        count=count-1
        return count
    
    def getImage(self,url,fileName):
        img=urllib.urlopen(url)
        data=img.read()
        imgFile=open(fileName, 'wb')
        imgFile.write(data)
        imgFile.close()

    def getPath(self):
        path = sys.path[0]
        if os.path.isdir(path):
           return path
        elif os.path.isfile(path):
           return os.path.dirname(path)

    def downloadAlbum(self,album):
        html=self.get(album)
        soup=BeautifulSoup(html,"html.parser")

        girlPath = self.getPath() + '//' + self.GirlID
        if(os.path.exists(girlPath)==False):
            os.mkdir(girlPath)
   
        albumPath = girlPath + '//' + album[-7:-1];
        if(os.path.exists(albumPath)==False): 
            os.mkdir(albumPath)

        count = self.getAlbumPagesCount(soup)
        images = []
        for i in range(0,count):
            html=self.get(album + str(i+1) + '.html')
            soup=BeautifulSoup(html,"html.parser")
            items=soup.find("div",class_="gallery_wrapper").find_all("img")
            for item in items:
                images.append(item['src'])

        index = 0
        for image in images:
            self.getImage(images[index],albumPath + '//' + str(index) + ".jpg")
            index +=1
    

    def download(self):
        html=self.get(self.GirlPage)
        soup=BeautifulSoup(html,"html.parser")
        self.getGirlName(soup)
        self.getGirlDesc(soup)
        self.getGirlAlbums(soup)
        self.getGirlStore(soup)

        threads = []
        for album in self.GirlAlbums:
            td = threading.Thread(target=self.downloadAlbum,args=(album,))
            threads.append(td)

        for td in threads:
            td.setDaemon(True)
            td.start()

if __name__ == '__main__':
    girl=ZNGirls('16702')
    girl.download()
