import requests
from requests.adapters import HTTPAdapter
import os
import re
import sys
import uuid
import json
import random
import threading
import threadpool
import fake_useragent
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
        self.Session.mount('http://', HTTPAdapter(max_retries=3))
        self.Session.mount('https://', HTTPAdapter(max_retries=3))
        self.Session.headers['User-Agent'] = fake_useragent.UserAgent().random
        self.Proxies = self.getIpList()

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
        proxyIP = random.choice(self.Proxies)
        proxies = {
            'http': proxyIP,
            'https': proxyIP
        }
        response = self.Session.get(url, allow_redirects=False, timeout=10, proxies=None)
        response.encoding = 'utf-8'
        content = response.text
        return content
    
    # 获取图集页数
    def getAlbumPagesCount(self, soup):
        pages = soup.find_all(name="div", attrs={"id": 'pages'})[0].find_all("a")
        return len(pages) - 1
    
    # 获取图片
    def getImage(self, url, fileName, retries=5):
        try:
            proxyIP = random.choice(self.Proxies)
            proxies = {
                'http': proxyIP,
                'https': proxyIP
            }
            self.Session.headers["Referer"] = "https://www.nvshens.org"
            response = self.Session.get(url, allow_redirects=False, timeout=10, proxies=None)
            response.raise_for_status()
            data = response.content
            imgFile = open(fileName, 'wb')
            imgFile.write(data)
            imgFile.close()
            return True
        except:
            while retries > 0:
                retries -= 1
                if self.getImage(url, fileName, retries):
                    break
                else:
                    continue

    # 
    def getIpList(self, maxPage=10):
        if (os.path.exists('ipList.json')):
            with open('ipList.json','rt',encoding='utf-8') as fp:
                return json.load(fp)
        else:
            ipList = []
            page = 1
            while (page <= maxPage):
                response = requests.get(f'http://www.kuaidaili.com/free/inha/{page}')
                response.raise_for_status()
                soup = BeautifulSoup(response.text)
                trs = soup.find(name='table').find_all(name='tr')
                for tr in trs[1:]:
                    tds = tr.find_all(name='td')
                    ip = tds[0].text + ':' + tds[1].text
                    ipList.append(ip)
                page+=1
            with open('ipList.json','wt',encoding='utf-8') as fp:
                json.dump(ipList, fp)
            return ipList
    
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
            fileName = os.path.join(albumPath, f'{str(index)}.jpg')
            args.append((None, {'url': url, 'fileName': fileName}))
        
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
        for girlId in sys.argv[1:]:
            girl = ZNGirls(girlId)
            girl.downloadAll()
