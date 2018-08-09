from PyQt5.QtWidgets import *
import threading
import sys
import os
import requests
import time
import re
import ctypes
import inspect
from bs4 import BeautifulSoup as bs

data = {
    'username': '',
    'password': '',
    'keeppwd': 'keepPwd',
    'app': ''}


class SpiderUI(QWidget):
    def __init__(self):
        self.GetCount = 0
        self.ThreadPool = []
        self.DownloadCount = 0
        self.loseCount = 0
        self.name = 'None'
        self.stop = False
        super().__init__()
        self.setWindowTitle('cnkiSpider v1.01')
        self.initUI()
        self.setFixedSize(300, 300)
        self.center()
        self.show()

    def initUI(self):
        reviewsPositionY = 200
        self.PaperNameLabel = QLabel('请输入英文报纸简称:', self)
        self.PaperNameLabel.move(10, 10)
        # self.PaperNameLabel.show()

        self.PaperName = QLineEdit(self)
        self.PaperName.move(10, 30)
        self.PaperName.setText('SXJJ')
        # self.PaperName.show()

        self.dateLabel = QLabel('输入开始日期(20120101):(可输入年份下载全年)', self)
        self.dateLabel.move(10, 60)
        # self.dateLabel.show()

        self.startdate = QLineEdit(self)
        self.startdate.move(10, 80)
        # self.startdate.show()

        self.enddateLabel = QLabel('输入结束日期(20120130):(输入同一年份)', self)
        self.enddateLabel.move(10, 100)
        # self.enddateLabel.show()

        self.enddate = QLineEdit(self)
        self.enddate.move(10, 120)
        # self.enddate.show()

        self.intervalLabel = QLabel('下载间隔(s):', self)
        self.intervalLabel.move(160, 10)

        self.interval = QLineEdit(self)
        self.interval.move(160, 30)
        self.interval.setText('2')

        self.DownloadCountLabel = QLabel('已下载数：', self)
        self.DownloadCountLabel.move(10, reviewsPositionY)

        self.DownloadCountindex = QLabel('0', self)
        self.DownloadCountindex.move(70, reviewsPositionY)

        self.loseCountlabel = QLabel('失败数:', self)
        self.loseCountlabel.move(10, reviewsPositionY+60)

        self.loseCountindex = QLabel('0', self)
        self.loseCountindex.move(70, reviewsPositionY+60)


        self.TotalNumLabel = QLabel('获取到的文件数:', self)
        self.TotalNumLabel.move(10, reviewsPositionY+20)

        self.TotalNum = QLabel('0', self)
        self.TotalNum.move(110, reviewsPositionY+20)

        self.DownloadButton = QPushButton('开始下载', self)
        self.DownloadButton.setGeometry(20, 150, 100, 50)
        self.DownloadButton.clicked.connect(self.Start)

        self.StopDownloadButton = QPushButton('停止下载', self)
        self.StopDownloadButton.setGeometry(150, 150, 100, 50)
        self.StopDownloadButton.clicked.connect(self.KillAllThread)
        # self.DownloadButton.show()

        self.ProcessLabel = QLabel('下载进度', self)
        self.ProcessLabel.move(10, reviewsPositionY+40)
        # self.ProcessLabel.show()


    def Start(self):
        t = threading.Thread(target=self.init, args=(int(self.startdate.text()),
                                            int(self.enddate.text()),
                                            self.PaperName.text(),
                                            float(self.interval.text())))

        self.ThreadPool.append(t)
        t.setDaemon(True)
        t.start()
        time.sleep(1)
        t1 = threading.Thread(target=self.refresh)
        t1.start()

    def center(self):
        # form a geometry equal to the main window(rectangle here)
        qr = self.frameGeometry()
        # get the middle point of screen
        cp = QDesktopWidget().availableGeometry().center()
        # move the rectangle to center of the screen
        qr.moveCenter(cp)
        # move the top-left point to the top-left point of the rectangle above(centering the window on our screen)
        self.move(qr.topLeft())

    def refresh(self):
        self.name_temp = ''
        while True:
            if self.name_temp != self.name:
                self.ProcessLabel.hide()
                self.ProcessLabel.setText(self.name)
                self.ProcessLabel.show()
                self.name_temp = self.name
            time.sleep(0.1)

    def clearAll(self):
        self.DownloadCount = 0
        self.GetCount = 0
        self.loseCount = 0

        self.DownloadCountindex.setText('0')
        self.TotalNum.setText('0')
        self.loseCountindex.setText('0')

#################################################################################################################################################


    def init(self, startdate=20120101, enddate=20120130, papername='SXJJ', interval=2):
        self.papername = papername
        self.s = requests.session()
        self.name = 'None'
        self.login_url = 'http://wap.cnki.net/touch/usercenter/Account/Validator'
        self.PaperId = []
        # self.locatePage('', '')

        self.PaperIdSet , self.PaperNamesSet = self.getArticleIDs(startdate, enddate+1, papername)
        self.login('blueking08', 'blueking007')
        self.main(self.PaperIdSet, self.PaperNamesSet, interval)
        selfthread = threading.current_thread()
        self.ThreadPool.remove(selfthread)

    # main download function, receive a list of download indexes
    def main(self, IDs, Names, interval=2):
        logPath = os.path.abspath('') + '/log.txt'
        dir_path = os.path.abspath('')+'/download'
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        savepath_raw = os.path.abspath('')+'/download/'
        for item in enumerate(IDs):
            try:
                self.name = Names[item[0]]
                self.name = '正在下载:' + self.name
                print('downloading:', item[1])
                savepath = savepath_raw + Names[item[0]] + '.pdf'
                if os.path.exists(savepath):
                    self.DownloadCount += 1
                    self.DownloadCountindex.setText(str(self.DownloadCount))
                    self.DownloadCountindex.adjustSize()
                    continue
                downurl = 'http://wap.cnki.net/touch/web/Download/Article?id=' + item[1] + '&dbtype=CCND&dbname=CCNDPTEM&uid='
                # print('downurl=', downurl)
                content = self.s.get(downurl).content
                f = open(savepath, 'wb')
                f.write(content)
                f.close()
                self.DownloadCount += 1
                self.DownloadCountindex.setText(str(self.DownloadCount))
                self.DownloadCountindex.adjustSize()
                time.sleep(interval)

            except (OSError, IOError):
                f1 = open(logPath, 'a+')
                f1.write(self.name+'\n \r\n')
                f1.close()
                self.loseCount += 1
                self.loseCountindex.setText(str(self.loseCount))
                self.loseCountindex.adjustSize()
                continue
    #login function
    def login(self, username, password):
        data['username'] = username
        data['password'] = password
        self.s.post(self.login_url, data=data)

    def getArticleIDs(self, startdate, enddate, papername):
        if startdate == enddate-1 and len(str(startdate)) == 4:
            ID, NE = self.getArticleIDsForYear(startdate, papername)
            return ID, NE
        final = []
        Names = []
        for i in range(startdate, enddate):
            Names_temp = []

            url = 'http://wap.cnki.net/touch/web/Newspaper/List/' + papername + str(i) + '.html'
            raw = self.s.get(url).content.decode('utf-8')

            b = bs(raw)
            tags = b.find_all(name='div', attrs={'class':'c-catalog__item-div'})

            for k in tags:
                for j in k.stripped_strings:
                    Names_temp.append(j)

            # attention! used needed first for more accurate match
            pattern = r'Newspaper/Article/' + self.papername[0] + '(.*?).html'
            IDs = re.findall(pattern, raw, re.S)
            # process the missing first back
            for u in IDs:
                self.paperID_full = self.papername[0] + u
                final.append(self.paperID_full)

            # pattern_name = r'item-div">"(.*?)"'
            #
            # Names_temp = re.findall(pattern_name, raw, re.S)
            #
            Names += Names_temp

            # if in one day more than 20 articles published, need a method to process the extra data.
            name_more_pattern = r'Title(.*?)\\",'  # need to cut 6 letter from begin with [6:]
            id_more_pattern = r'FileName\\":(.*?)\\"\\r\\n' # cut 3 letter with [3:]
            print('lenNamestemp=', len(Names_temp))
            if len(Names_temp) >= 20:
                name_more = []
                id_more = []
                data = {'id':self.papername+str(i)}
                moreUrl = 'http://wap.cnki.net/touch/web/api/CatalogApi/AllNewspaperCatalog'
                resp = requests.post(moreUrl, data=data)
                more_raw = resp.content.decode('utf-8')

                name_more_temp = re.findall(name_more_pattern, more_raw, re.S)
                for item in name_more_temp:
                    name_more.append(item[6:])
                Names += name_more

                id_more_temp = re.findall(id_more_pattern, more_raw, re.S)
                for item in id_more_temp:
                    id_more.append(item[3:])
                final += id_more

            print('lenNames=', len(Names_temp))
            print('Getting:', i)
            self.name = 'Getting:' + str(i)

        # process special symbols
        for checkitem in enumerate(Names):
            Names[checkitem[0]] = Names[checkitem[0]].replace('*', '()')
            Names[checkitem[0]] = Names[checkitem[0]].replace('?', '(？)')
            Names[checkitem[0]] = Names[checkitem[0]].replace('\r', 'R')
            Names[checkitem[0]] = Names[checkitem[0]].replace('\n', 'N')
            Names[checkitem[0]] = Names[checkitem[0]].replace(':', '(：)')
            Names[checkitem[0]] = Names[checkitem[0]].replace('\\', 'l')
            Names[checkitem[0]] = Names[checkitem[0]].replace('<', '小于')
            Names[checkitem[0]] = Names[checkitem[0]].replace('>', '大于')
            Names[checkitem[0]] = Names[checkitem[0]].replace('|', 'l')
            Names[checkitem[0]] = Names[checkitem[0]].replace('”', '(引号)')
            Names[checkitem[0]] = Names[checkitem[0]].replace('“', '(引号)')
            Names[checkitem[0]] = Names[checkitem[0]].replace('"', '(引号)')
            Names[checkitem[0]] = Names[checkitem[0]].replace('/', '(斜杠)')
            Names[checkitem[0]] = Names[checkitem[0]].replace('%', '(百分号)')
            Names[checkitem[0]] = Names[checkitem[0]].replace(' ', 'o')


        print(Names)

        print(len(final))
        print(len(Names))

        self.GetCount += len(final)

        self.TotalNum.setText(str(self.GetCount))
        self.TotalNum.adjustSize()

        # final is the IDSet. Names is the chinese title of the articles.
        return final, Names

    def getArticleIDsForYear(self, year, papername):
        year = str(year)
        tempIDs, tempNEs = [], []
        IDs,Names = [], []
        monthStart = ['0101', '0201', '0301', '0401', '0501', '0601', '0701', '0801', '0901', '1001', '1101', '1201']
        monthEnd = ['0131', '0229', '0331', '0430', '0531', '0630', '0731', '0831', '0930', '1031', '1130', '1231']
        for i in range(0, 12):
            tempIDs, tempNEs = self.getArticleIDs(int(year+monthStart[i]), int(year+monthEnd[i])+1, papername)
            IDs += tempIDs
            Names += tempNEs

        return IDs, Names



    def _async_raise(self, tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def stop_thread(self, thread):
        self._async_raise(thread.ident, SystemExit)

    def KillAllThread(self):
        for babies in self.ThreadPool:
            self.stop_thread(babies)
            time.sleep(0.2)
        self.ThreadPool = []

    def closeEvent(self, event):
        self.KillAllThread()
        event.accept()


if __name__ == '__main__':
    a = QApplication(sys.argv)
    e = SpiderUI()
    sys.exit(a.exec_())