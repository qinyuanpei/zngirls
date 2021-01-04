import requests
import os
import re
import sys
import uuid
import random
import threading
import threadpool

from bs4 import BeautifulSoup


class ZNGirls:

    def __init__(self, id):
        self.GirlID = str(id)
        self.GirlName = ''
        self.GirlPage = f'https://www.nvshens.org/girl/{self.GirlID}/'
        self.GirlPath = ''
        self.GirlDesc = ''
        self.GirlInfo = {}
        self.GirlAlbums = []
        self.GirlSocial = []
        self.GirlStore = ''
        self.Session = requests.session()
        self.Session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'

    def getGirlName(self, soup):
        self.GirlName = soup.find(
            name='div', attrs={"class": "div_h1"}).h1.string

    def getGirlPage(self):
        return self.GirlPage

    def getGirlDesc(self, soup):
        self.GirlDesc = soup.find(
            name='div', attrs={"class": "infocontent"}).find("p").string
        print(self.GirlDesc)

    def getGirlAlbums(self, soup):
        archives = soup.find_all(name="span", attrs={"class": "archive_more"})
        is_allAlbums = len(archives) <= 0
        if(is_allAlbums == False):
            archive_url = self.GirlPage + 'album/'
            html = self.get(archive_url)
            soup = BeautifulSoup(html)

        for albumLink in soup.find_all(name="a", attrs={"class": "igalleryli_link"}):
            album = {}
            album["Id"] = str(albumLink['href'])
            album['Url'] = f'https://www.nvshens.org/{album["Id"]}'
            album['Title'] = albumLink.img['alt']
            rstr = r"[\/\\\:\*\?\"\<\>\|]"
            album['Title'] = re.sub(rstr, "_", album['Title'])  # 替换为下划线
            self.GirlAlbums.append(album)

    def getGirlStore(self, soup):
        self.GirlStore = soup.find(
            name="span", attrs={"class": "score"}).contents[0]
        print(self.GirlStore)

    def getGirlAlbumName(self, soup):
        return soup.find(name="div", attrs={"class": "albumTitle"}).h1.string

    def getGirlInfo(self, soup):
        table = soup.find(name='div', attrs={"class": "infodiv"}).table
        if table != None:
            for row in table.find_all('tr'):
                cols = row.contents
                self.GirlInfo[cols[0].text.strip()] = cols[1].text.strip()
        print(self.GirlInfo)

    def get(self, url):
        response = self.Session.get(url, allow_redirects=False)
        response.encoding = 'utf-8'
        content = response.text
        return content

    def getAlbumPagesCount(self, soup):
        pages = soup.find_all(name="div", attrs={"id": 'pages'})[
            0].find_all("a")
        count = len(pages)
        count = count-1
        return count

    def getImage(self, url, fileName):
        response = self.Session.get(url, allow_redirects=False)
        response.raise_for_status()
        data = response.content
        imgFile = open(fileName, 'wb')
        imgFile.write(data)
        imgFile.close()

    def getPath(self):
        path = sys.path[0]
        if os.path.isdir(path):
            return path
        elif os.path.isfile(path):
            return os.path.dirname(path)

    def downloadAlbum(self, album):
        html = self.get(album['Url'])
        soup = BeautifulSoup(html)

        girlPath = os.path.join(self.getPath(), self.GirlName)
        if(os.path.exists(girlPath) == False):
            os.mkdir(girlPath)

        albumPath = os.path.join(girlPath, album['Title'])
        if(os.path.exists(albumPath) == False):
            os.mkdir(albumPath)

        count = self.getAlbumPagesCount(soup)
        images = []
        for i in range(0, count):
            html = self.get(album['Url'] + str(i+1) + '.html')
            soup = BeautifulSoup(html)
            items = soup.find(name="div", attrs={
                              "class": "gallery_wrapper"}).find_all("img")
            for item in items:
                images.append(item['src'].replace('/s/', '/'))

        args = []
        for index, url in enumerate(images):
            args.append(
                (None, {'url': url, 'fileName': albumPath + '//' + str(index) + ".jpg"}))
        pool = threadpool.ThreadPool(max(10, len(images)))
        requests = threadpool.makeRequests(self.getImage, args)
        [pool.putRequest(req) for req in requests]
        pool.wait()

    def downloadAll(self):
        html = self.get(self.GirlPage)
        soup = BeautifulSoup(html)
        self.getGirlName(soup)
        self.getGirlDesc(soup)
        self.getGirlAlbums(soup)
        self.getGirlInfo(soup)
        self.getGirlStore(soup)
        print(f'{self.GirlName} {self.GirlStore}\n')
        print(
            '\n'.join(map(lambda x: f'{x[0]} {x[1]}', self.GirlInfo.items())))
        if (self.getGirlDesc != None):
            print(f'{self.GirlDesc}\n')

        albumLen = len(self.GirlAlbums)
        pool = threadpool.ThreadPool(max(10, albumLen))
        requests = threadpool.makeRequests(self.downloadAlbum, self.GirlAlbums)
        [pool.putRequest(req) for req in requests]
        pool.wait()
        # for album in self.GirlAlbums:
        # td = threading.Thread(target=self.downloadAlbum,args=(album,))
        # threads.append(td)
        # self.downloadAlbum(album)

        # for td in threads:
        #     td.setDaemon(True)
        #     td.start()

    def download(self, album):
        albumURL = 'https://www.nvshens.org/g/' + album + '/'

        threads = []
        td = threading.Thread(target=self.downloadAlbum, args=(albumURL,))
        threads.append(td)

        for td in threads:
            td.setDaemon(True)
            td.start()

    def random(self):
        response = self.Session.get('https://www.nvshens.org/meet')
        self.GirlID = response.headers['location'].split('/')[-1]
        self.downloadAll()


if __name__ == '__main__':
    girl = ZNGirls('25101')
    girl.downloadAll()
    # girl.random();
