from PyQt5.QtWidgets import *
import threading
import sys
import os
import requests
import time
import re
from bs4 import BeautifulSoup as bs

data = {
    'username': '',
    'password': '',
    'keeppwd': 'keepPwd',
    'app': ''}


class SpiderUI(QWidget):
    def __init__(self):
        self.name = 'None'
        self.stop = False
        super().__init__()
        self.setWindowTitle('cnkiSpider v1.0')
        self.initUI()
        self.setFixedSize(300, 250)
        self.center()
        self.show()

    def initUI(self):
        self.PaperNameLabel = QLabel('请输入英文报纸简称:', self)
        self.PaperNameLabel.move(10, 10)
        # self.PaperNameLabel.show()

        self.PaperName = QLineEdit(self)
        self.PaperName.move(10, 30)
        self.PaperName.setText('SXJJ')
        # self.PaperName.show()

        self.dateLabel = QLabel('请输入开始日期(20120101):', self)
        self.dateLabel.move(10, 60)
        # self.dateLabel.show()

        self.startdate = QLineEdit(self)
        self.startdate.move(10, 80)
        # self.startdate.show()

        self.enddateLabel = QLabel('请输入结束日期(20120130):', self)
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

        self.TotalNumLabel = QLabel('获取到的文件数:', self)
        self.TotalNumLabel.move(10, 200)

        self.TotalNum = QLabel('0', self)
        self.TotalNum.move(110, 200)

        self.DownloadButton = QPushButton('开始下载', self)
        self.DownloadButton.setGeometry(100, 150, 100, 50)
        self.DownloadButton.clicked.connect(self.Start)
        # self.DownloadButton.show()

        self.ProcessLabel = QLabel('下载进度', self)
        self.ProcessLabel.move(10, 220)
        # self.ProcessLabel.show()


    def Start(self):
        t = threading.Thread(target=self.init, args=(int(self.startdate.text()),
                                            int(self.enddate.text()),
                                            self.PaperName.text(),
                                            float(self.interval.text())))

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



#################################################################################################################################################


    def init(self, startdate=20120101, enddate=20120130, papername='SXJJ', interval=2):
        self.papername = papername
        self.s = requests.session()
        self.name = 'None'
        # self.getArticleIDs(20120101, 20120131)
        self.login_url = 'http://wap.cnki.net/touch/usercenter/Account/Validator'
        self.PaperId = []
        # self.locatePage('', '')

        self.PaperIdSet , self.PaperNamesSet = self.getArticleIDs(startdate, enddate, papername)
        self.login('blueking08', 'blueking007')
        self.main(self.PaperIdSet, self.PaperNamesSet, interval)

    # main download function, receive a list of download indexes
    def main(self, IDs, Names, interval=2):
        dir_path = os.path.abspath('')+'/download'
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        savepath_raw = os.path.abspath('')+'/download/'
        for item in enumerate(IDs):
            self.name = Names[item[0]]
            self.name = '正在下载:' + self.name

            print('downloading:', item[1])
            savepath = savepath_raw + Names[item[0]] + '.pdf'
            downurl = 'http://wap.cnki.net/touch/web/Download/Article?id=' + item[1] + '&dbtype=CCND&dbname=CCNDPTEM&uid='
            # print('downurl=', downurl)
            content = self.s.get(downurl).content
            f = open(savepath, 'wb')
            f.write(content)
            f.close()
            time.sleep(interval)
        self.stop = True
    #login function
    def login(self, username, password):
        data['username'] = username
        data['password'] = password
        self.s.post(self.login_url, data=data)




    def getArticleIDs(self, startdate, enddate, papername):
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


        for checkitem in enumerate(Names):
            if '\r' in Names[checkitem[0]] or '\\' in Names[checkitem[0]] or '/' in Names[checkitem[0]] or '\n' in Names[checkitem[0]]:
                Names[checkitem[0]] = 'manu' + checkitem[1]
        print(Names)
        # check the content of the lists
        # print('final=')
        # for i in final:
        #     print(i)
        # print('Names=')
        # for i in Names:
        #     print(i)

        # check for the length of two lists
        print(len(final))
        print(len(Names))
        self.TotalNum.setText(str(len(final)))
        self.TotalNum.adjustSize()

        # final is the IDSet. Names is the chinese title of the articles.
        return final, Names



if __name__ == '__main__':
    a = QApplication(sys.argv)
    e = SpiderUI()
    sys.exit(a.exec_())