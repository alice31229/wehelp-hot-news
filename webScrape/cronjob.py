import sched
import threading
import time

from webScrape.ptt import get_pttbrain
from webScrape.udn import get_udn
from webScrape.storm import get_storm
from webScrape.businesstoday import get_businesstoday


def main():
    scheduler = sched.scheduler(time.time, time.sleep)

    # 每晚12點執行四支爬蟲程式
    scheduler.enter(0, 1, get_pttbrain, ())
    scheduler.enter(0, 1, get_udn, ())
    scheduler.enter(0, 1, get_storm, ())
    scheduler.enter(0, 1, get_businesstoday, ())

    # 四個流程
    t1 = threading.Thread(target=scheduler.run)
    t2 = threading.Thread(target=scheduler.run)
    t3 = threading.Thread(target=scheduler.run)
    t4 = threading.Thread(target=scheduler.run)

    # 啟動流程
    t1.start()
    t2.start()
    t3.start()
    t4.start()

    # 等待流程結束
    t1.join()
    t2.join()
    t3.join()
    t4.join()

if __name__ == '__main__':
    main()