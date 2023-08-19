# https://blog.51cto.com/u_14210396/6456678
import re
import random
import warnings
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By
import requests
import sqlite3
from lxml import etree
import pandas as pd
import datetime


warnings.filterwarnings('ignore')


def html_has_xpath(html_str, xpath):
    try:
        html_str.xpath(xpath)
    except:
        flag = False
    else:
        flag = True
    return flag


def has_xpath_list(html_str, xpath):
    flag = False
    try:
        res = html_str.xpath(xpath)
    except:
        flag = False
    else:
        if isinstance(res, list) and len(res) > 0:
            flag = True
    return flag


def get_now():
    now = datetime.datetime.now()
    date = now.strftime("%Y_%m_%d_%H_%M")
    return date


def get_element_text(html_str, xpath, default='未知', index=0):
    try:
        res = html_str.xpath(xpath)
    except:
        text = default
    else:
        if isinstance(res, list) and len(res) > 0:
            text = html_str.xpath(xpath)[index].text
        else:
            text = default
    return text


def get_child_element_by_class_name(parent_element, class_name):
    try:
        child_element = parent_element.find_element(By.CLASS_NAME, class_name)
    except:
        pass
    else:
        return child_element



def get_child_element_text_by_class_name(parent_element, class_name):
    child_element = get_child_element_by_class_name(parent_element, class_name)
    try:
        text = child_element.text
    except:
        text = ''
    return text

class LiePin:
    def __init__(self, queries,
                 locations=('全国', ),
                 cookie='',
                 need_login=False,
                 max_page_num=20,
                 retries=3):
        # 岗位列表
        self.driver = None
        self.post_list = queries
        self.locations = locations
        self.cookie = cookie
        self.retries = retries
        self.max_page_num = max_page_num
        self.now = get_now()
        # 岗位链接列表
        self.all_link = []
        self.liepin_url = 'https://www.liepin.com/zhaopin/'

        # 等待3三秒
        self.search_list_file = f'PostUrls/job_url_{self.now}.xlsx'
        self.job_detail_file = f'PostIntroduceDatas/job_detail_{self.now}.xlsx'

        # 随机用户(User_Agent)
        with open('User_Agent_pool.txt', 'r', encoding='utf8') as fp:
            self.user_Agent = fp.readlines()
            self.user_Agent = [line.strip() for line in self.user_Agent]

        self.init(need_login=need_login)


    def init(self, need_login=False):
        self.driver = webdriver.Chrome()
        time.sleep(2)
        self.driver.get(self.liepin_url)
        if need_login:
            self.login()
        time.sleep(4)

    def login(self):
        sucess_flag = ('yes', 'y')
        flag = ''
        while flag.lower() not in sucess_flag:
            flag = input('请手动登录\n<输入 "yes", 确认已登录>\n')
        if flag in ('yes', 'y'):
            self.refresh()


    def refresh(self, url=None):
        if url:
            self.driver.get(url)
        else:
            self.driver.refresh()
        time.sleep(3)


    def quit(self):
        self.driver.quit()

    def get_post_link(self, post, city='全国'):
        print("===========开始爬取", post, city, "岗位链接===========")
        # 搜索筛选条件
        # 按城市
        search_city_box = self.driver.find_element(By.XPATH, "//div[@id='lp-search-job-box']/div[2]/div[1]/div[2]/ul")

        for li in search_city_box.find_elements(By.CLASS_NAME, 'options-item'):
            if li.text == city:
                li.click()
                break

        # 定位搜索框并输入关键词
        search_box = self.driver.find_element(By.XPATH, "//div[@id='lp-search-bar-section']//input")
        search_box.send_keys(post)
        search_box.send_keys(Keys.RETURN)

        # 获取最大的页码
        try:
            page_size_box = driver.find_element(By.XPATH, "//*[@id='lp-search-job-box']/div[3]/section[1]/div[2]/ul")
            page_num = int(page_size_box.find_elements(By.CLASS_NAME, 'ant-pagination-item')[-1].text)
        except:
            page_num = 10
        print(f'"{post}" 相关的岗位在 {city} 有 {page_num} 页')

        # 结果数据
        result = []
        for page in range(page_num):
            print("开始爬取第", page + 1, "页链接…………")
            # 等待页面加载完成
            time.sleep(3)
            # 读取当前页岗位数量
            divs = self.driver.find_elements(By.XPATH, "//div[@class='content-wrap']//div[@class='job-list-box']/div")
            for i in range(1, len(divs) + 1):
                link = self.driver.find_element(By.XPATH, f"//div[@class='job-list-box']/div[{i}]//a").get_attribute("href")
                # 存储岗位链接信息

                e = self.driver.find_element(By.XPATH, f"//*[@id='lp-search-job-box']/div[3]/section[1]/div[1]/div[{i}]")

                # 是否广告
                ads = get_child_element_text_by_class_name(e, "ad-flag-box")

                # 工作地址：
                post_location = self.driver.find_element(By.XPATH, f"//*[@id='lp-search-job-box']/div[3]/section[1]/div[1]/div[1]/div/div[1]/div/a/div[1]/div/div[2]/span[2]").text

                # 岗位名称：
                post_name = self.driver.find_element(By.XPATH, "//*[@id='lp-search-job-box']/div[3]/section[1]/div[1]/div[1]/div/div[1]/div/a/div[1]/div/div[1]").text


                job_tag = get_child_element_text_by_class_name(e, "job-tag")

                # 薪资
                post_salary = get_child_element_text_by_class_name(e, "job-salary")

                # 岗位标签:
                _labels_element = e.find_elements(By.CLASS_NAME, 'labels-tag')
                labels_tag = ', '.join([e.text for e in _labels_element])

                # 招聘人
                hr_name = get_child_element_text_by_class_name(e, "recruiter-name")

                # 招聘人title
                hr_title = get_child_element_text_by_class_name(e, "recruiter-title")

                # 公司标签
                company_tag_html = get_child_element_by_class_name(e, "company-tags-box").get_attribute("innerHTML")
                pattern = r'<span[^>]*>([^<]+)</span>'
                company_tags = ', '.join(re.findall(pattern, company_tag_html))

                # 用人单位
                enterprise_name = get_child_element_text_by_class_name(e, "company-name")

            result.append([post, city, post_name, post_location, job_tag, post_salary, labels_tag,
                               hr_name, hr_title,
                               enterprise_name, company_tags, ads, str(link)])


            # 爬取下一页
            time.sleep(3 + random.random() * 4)
            if page >= self.max_page_num - 1:
                break

            try:
                page_size_box = self.driver.find_element(By.XPATH, "//*[@id='lp-search-job-box']/div[3]/section[1]/div[2]/ul")
                next_page_element = page_size_box.find_elements(By.CLASS_NAME, "ant-pagination-item-link")[-1]
            except Exception as e:
                is_page_turned = False
                print('Error： 首次尝试翻页失败')
                print(e)
            else:
                if next_page_element.is_enabled():
                    next_page_element.click()
                    is_page_turned = True
                else:
                    is_page_turned = False
                    print('首次尝试翻页失败')

            if not is_page_turned:
                try:
                    self.driver.find_element(By.XPATH, "//div[@class='list-pagination-box']//li["
                                                    "@class='ant-pagination-next']/button").click()
                except Exception as e:
                    is_page_turned = False
                    print('Error： 再次尝试翻页失败')
                    print(e)
                else:
                    is_page_turned = True

            if not is_page_turned:
                print(f'==========================停止对 "{post}" 相关岗位在 {city} 的搜索==========================')
                break

        return result


    # 爬取岗位详情信息
    def get_post_detail(self, search_list_file=None):
        print("==========================开始提取各岗位详情页信息==========================")
        if search_list_file:
            self.search_list_file = search_list_file
        df_info = pd.read_excel(self.search_list_file)
        print(f'找到 {df_info.shape[0]} 个需提取详情的 URL')
        df_info = df_info.drop_duplicates(subset=['url'])
        print(f'剔除重复的url，还剩下 {df_info.shape[0]} 个 URL 待处理')
        result, error_url = [], []
        for post, group in df_info.groupby('搜索词'):
            print("++++++++++++开始获取", post, "相关岗位详情信息++++++++++++")
            loop = self.retries
            urls = group['url'].values.tolist()
            p_result = []
            _error_url = urls
            while loop > 0 and _error_url:
                _result, _error_url = self._get_post_detail(urls=_error_url, post=post)
                p_result.extend(_result)
                loop -= 1
                time.sleep(3)
            result.extend(p_result)
            error_url.extend(_error_url)
        print('==================',
              '成功获取 {} 个岗位详情数据'.format(len(result)),
               '失败 {} 个'.format(len(error_url)),
              '==================')

        df_out = pd.DataFrame(result)
        df_out.to_excel(self.job_detail_file, index=False)
        print(f'结果保持到 {self.job_detail_file}')
        error_url_file = 'error_url/error_message_{}.txt'.format(self.now)
        with open(error_url_file,
                  'a+', encoding='utf-8') as f:
            for url in error_url:
                f.write(url)
        print(f'错误 url 保持到 {error_url_file}')

    # 爬取岗位详情信息
    def _get_post_detail(self, urls, post, retries=3):
        index = 0
        result = []
        error_url = []
        for url in urls:
            index += 1
            print(f"提取{post}岗位,第", index, "条数据……")
            time.sleep(1 + random.random())
            detail = {}
            _retries = retries
            while not detail.get('status') and _retries > 0:
                try:
                    # 发送GET请求
                    headers = {"User-Agent": random.choice(self.user_Agent)}
                    if self.cookie:
                        headers["Cookie"] = self.cookie
                    response = requests.get(url=url, headers=headers, timeout=10)
                    html_str = etree.HTML(response.text)
                    # 岗位链接
                    post_link = str(url)
                    # 搜索岗位名
                    search_name = post
                    detail = self.parse_page(html_str, post_link, search_name)
                    _retries -= 1
                    time.sleep(1 + random.random())
                except Exception as e:
                    print('爬取失败：{}\nurl: {}'.format(e, url))

            if detail.get('status'):
                result.append(detail)
            else:
                error_url.append(url)
        return result, error_url


    def parse_page(self, html_str, post_link, search_name):
        detail = {}
        try:
            # 岗位名称
            post_name = get_element_text(html_str, "//body/section[3]//div[@class='name-box']/span[1]", "未知")

            # 企业名称
            enterprise_name = get_element_text(html_str, "//aside//div[@class='company-info-container']//div["
                                                         "contains(@class,'name')]", "未知")

            # 企业经营范围
            enterprise_scope = get_element_text(html_str, "//aside//div[@class='register-info']/div[contains(@class,"
                                                          "'ellipsis-4')]/span[2]", "未知")
            # 薪资区间
            post_salary = get_element_text(html_str, "//body/section[3]//div[@class='name-box']/span[@class='salary']",'未知')

            # 工作地点
            post_location = get_element_text(html_str, "//body/section[3]//div[@class='job-properties']/span[1]",'未知')
            # 工作经验

            work_experience = get_element_text(html_str, "//body/section[3]//div[@class='job-properties']/span[3]",'未知')

            # 学历要求
            educational_requirements = get_element_text(html_str, "//body/section[3]//div[@class='job-properties']/span[5]",'未知')

            # 其他待遇
            about_treatment = ''
            if has_xpath_list(html_str, "//body/section[4]//div[@class='labels']/span"):
                for sub in html_str.xpath("//body/section[4]//div[@class='labels']/span"):
                    about_treatment += ' ' + sub.text

            # 岗位介绍
            post_introduce = get_element_text(html_str, "//main//dl[1]/dd", '未找到')

            # 招聘人的姓名
            hr_name = get_element_text(html_str, '//body/main/content/section[1]/div[2]/div[1]/span[1]', '未知')

            # 是否认证
            hr_is_official = get_element_text(html_str, '//body/main/content/section[1]/div[2]/div[1]/span[3]','未认证')

            # 最近的上线时间
            hr_active_time = get_element_text(html_str, '//body/main/content/section[1]/div[2]/div[1]/span[2]', '未知')

            # 招聘人的岗位
            hr_title = get_element_text(html_str, '//body/main/content/section[1]/div[2]/div[2]/span[1]', '未知')

            # 招聘人挂靠的公司
            hr_company_name = '未知'
            if has_xpath_list(html_str, '//body/main/content/section[1]/div[2]/div[2]/span[2]'):
                hr_company_element = html_str.xpath('//body/main/content/section[1]/div[2]/div[2]/span[2]')[0]
                if hr_company_element.getchildren():
                    hr_company_element = hr_company_element.getchildren()[0] # 处理有链接的公司名称
                hr_company_name = hr_company_element.text.strip()

            # 招聘人的系统标签
            hr_labels = []
            if has_xpath_list(html_str, '//body/main/content/section[1]/div[2]/div[3]'):
                hr_label_element = html_str.xpath('//body/main/content/section[1]/div[2]/div[3]')[0]
                for e in hr_label_element.getchildren():
                    hr_labels.append(e.text)
            hr_labels = ', '.join(hr_labels)

            # 岗位标签
            job_labels = []
            if has_xpath_list(html_str, '//body/main/content/section[2]/dl[1]/div/ul'):
                job_labels_element = html_str.xpath('//body/main/content/section[2]/dl[1]/div/ul')[0]
                for e in job_labels_element.getchildren():
                    job_labels.append(e.text)
            job_labels = ', '.join(job_labels)

            # 其他信息
            other_info = []
            if has_xpath_list(html_str, '//body/main/content/section[2]/dl[2]'):
                other_info_element = html_str.xpath('//body/main/content/section[2]/dl[2]')[0]
                for e in other_info_element.getchildren():
                    other_info.append(e.text)
            other_info = '\n'.join(other_info)

            # 保存数据
            # self.save_data(post_link, )
            detail = {
                "岗位链接": post_link,
                "搜索岗位名": search_name,
                "岗位名称": post_name,
                "岗位标签": job_labels,
                "企业名称": enterprise_name,
                "薪资区间": post_salary,
                "工作地点": post_location,
                "工作经验": work_experience,
                "学历要求": educational_requirements,
                "岗位介绍": post_introduce,
                "岗位其他信息": other_info,
                "其他待遇": about_treatment,
                "企业经营范围": enterprise_scope,
                "招聘人的姓名": hr_name,
                "招聘人的岗位": hr_title,
                "招聘人的组织": hr_company_name,
                "招聘人是否认证": hr_is_official,
                "招聘人最近的上线时间": hr_active_time,
                "招聘人的系统标签": hr_labels
            }
        except Exception as e:
            print('网页解析错误', e)
        if detail and detail.get('岗位名称') != '未知':
            detail['status'] = 'ok'
        return detail


    def scrapy_brief_job_info(self):
        # 爬取各岗位链接
        data = []
        for post in self.post_list:
            for location in self.locations:
                _res = self.get_post_link(post=post, city=location)
                data.extend(_res)
                time.sleep(2)
                self.refresh(url=self.liepin_url)

        if len(data) > 0:
            df_info = pd.DataFrame(data, columns=['搜索词', "筛选地点", '岗位名称', "工作地点", "招聘标签", "薪资区间",
                                                  "岗位标签", "招聘人的姓名", "招聘人的岗位",
                                                  "企业名称", "企业标签", "是否广告", "url"])
            df_info.to_excel(self.search_list_file, index=False)


    def run(self):
        self.login()
        self.scrapy_brief_job_info()
        self.get_post_detail()
        self.quit()


if __name__ == '__main__':
    queries = ['aigc算法']
    locations = ['全国', '北京', '深圳', '武汉', '广州', '上海', '杭州']
    cookie = ''
    liepin = LiePin(queries=queries,
                    locations=locations, cookie=cookie, max_page_num=3, retries=3)
    liepin.run()
    print("数据采集完毕！")
