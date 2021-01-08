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
        self.GirlScore = ''
        self.Session = requests.session()
        self.Session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'

    # 获取妹子姓名
    def getGirlName(self, soup):
        return soup.find(name='div', attrs={"class": "div_h1"}).h1.string

    # 获取妹子描述
    def getGirlDesc(self, soup):
        return soup.find(name='div', attrs={"class": "infocontent"}).find("p").string
    
    # 获取妹子图集
    def getGirlAlbums(self, soup):
        archives = soup.find_all(name="span", attrs={"class": "archive_more"})
        is_allAlbums = len(archives) <= 0
        if  not is_allAlbums:
            archive_url = self.GirlPage + 'album/'
            html = self.get(archive_url)
            soup = BeautifulSoup(html)

        for albumLink in soup.find_all(name="a", attrs={"class": "igalleryli_link"}):
            album = {}
            album["Id"] = str(albumLink['href'])
            album['Url'] = f'https://www.nvshens.org/{album["Id"]}'
            album['Title'] = albumLink.img['alt']
            rstr = r"[\/\\\:\*\?\"\<\>\|]"
            album['Title'] = re.sub(rstr, "_", album['Title'])  # 替换路径中的特殊字符为下划线
            yield album
    
    # 获取妹子评分
    def getGirlScore(self, soup):
        return soup.find(name="span", attrs={"class": "score"}).contents[0]
    
    # 获取图集名称
    def getGirlAlbumName(self, soup):
        return soup.find(name="div", attrs={"class": "albumTitle"}).h1.string
    
    # 获取妹子信息
    def getGirlInfo(self, soup):
        girlInfo = {}
        table = soup.find(name='div', attrs={"class": "infodiv"}).table
        if table != None:
            for row in table.find_all('tr'):
                cols = row.contents
                girlInfo[cols[0].text.strip()] = cols[1].text.strip()
        return girlInfo
    
    # 获取HTML
    def get(self, url):
        response = self.Session.get(url, allow_redirects=False)
        response.encoding = 'utf-8'
        content = response.text
        return content
    
    # 获取图集页数
    def getAlbumPagesCount(self, soup):
        pages = soup.find_all(name="div", attrs={"id": 'pages'})[0].find_all("a")
        return len(pages) - 1
    
    # 获取图片
    def getImage(self, url, fileName):
        response = self.Session.get(url, allow_redirects=False)
        response.raise_for_status()
        data = response.content
        imgFile = open(fileName, 'wb')
        imgFile.write(data)
        imgFile.close()
    
    # 获取当前目录
    def getPath(self):
        path = sys.path[0]
        if os.path.isdir(path):
            return path
        elif os.path.isfile(path):
            return os.path.dirname(path)

    # 下载指定图集
    def downloadAlbum(self, album):
        albumUrl = album['Url']
        albumTitle = album['Title']

        html = self.get(albumUrl)
        soup = BeautifulSoup(html)

        # 为每个妹子建一个目录
        girlPath = os.path.join(self.getPath(), self.GirlName)
        if not os.path.exists(girlPath):
            os.mkdir(girlPath)
        
        # 为一个图集建一个目录
        albumPath = os.path.join(girlPath, albumTitle)
        if not os.path.exists(albumPath):
            os.mkdir(albumPath)
        
        # 抓取图片链接
        total = self.getAlbumPagesCount(soup)
        images = []
        for i in range(0, total):
            html = self.get(album['Url'] + str(i+1) + '.html')
            soup = BeautifulSoup(html)
            items = soup.find(name="div", attrs={"class": "gallery_wrapper"}).find_all("img")
            for item in items:
                images.append(item['src'].replace('/s/', '/'))

        args = []
        for index, url in enumerate(images):
            args.append((None, {'url': url, 'fileName': albumPath + '//' + str(index) + ".jpg"}))
        pool = threadpool.ThreadPool(max(10, len(images)))
        requests = threadpool.makeRequests(self.getImage, args)
        [pool.putRequest(req) for req in requests]
        pool.wait()

    def downloadAll(self):
        html = self.get(self.GirlPage)
        soup = BeautifulSoup(html)
        self.GirlName = self.getGirlName(soup)
        self.GirlDesc = self.getGirlDesc(soup)
        self.GirlAlbums = list(self.getGirlAlbums(soup))
        self.GirlInfo = self.getGirlInfo(soup)
        self.GirlScore = self.getGirlScore(soup)

        albumLen = len(self.GirlAlbums)
        maxNum = 5
        if albumLen < maxNum:
           maxNum = albumLen
        pool = threadpool.ThreadPool(maxNum)
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
    if len(sys.argv) > 1:
        print(sys.argv[1:])
        for girlId in sys.argv[1:]:
            girl = ZNGirls(girlId)
            girl.downloadAll()
