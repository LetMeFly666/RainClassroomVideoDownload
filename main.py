'''
Author: LetMeFly
Date: 2023-07-01 15:34:34
LastEditors: LetMeFly
LastEditTime: 2023-07-01 18:02:13
'''
import requests
import os

Config = {
    'Cookie': 'sessionid=498e8384w849q948q121x884ffe78ett',
    'CourseId': '16809342',  # cid https://grsbupt.yuketang.cn/pro/lms/84eubUaed9T/16809342/studycontent
    'Sign': '84eubUaed9T',  # https://grsbupt.yuketang.cn/pro/lms/84eubUaed9T/16809342/studycontent
    'Domain': 'grsbupt.yuketang.cn',  # https://grsbupt.yuketang.cn/pro/lms/84eubUaed9T/16809342/studycontent
    'uv_id': '3090',  # 意义暂不明确
    'SaveDirName': 'LetYuOutput',  # 视频要保存到的文件夹，存在则直接保存，不存在则创建
}


def launct1request(url):
    print(url)
    """携带cookie等header发送请求并返回结果"""
    return requests.get(
        url=url,
        headers={
            'Cookie': Config['Cookie'],
            'Xtbz': 'cloud',
        },
    )


def getVideoList():
    """
    以列表的形式返回每一个video的内容
    将会丢失掉章节信息、非video信息
    """
    response = launct1request(f'https://{Config["Domain"]}/mooc-api/v1/lms/learn/course/chapter?cid={Config["CourseId"]}&sign={Config["Sign"]}&uv_id={Config["uv_id"]}')
    videoList = []
    print(response)

    def appendVideoOrNot(videoInfoList):
        if str(videoInfoList.get('leaf_type', -1)) == '0':  # 0视频  6作业
            videoList.append({'urlId': videoInfoList['id'], 'videoName': videoInfoList['name']})
    
    for courseChapter in response.json()['data']['course_chapter']:
        appendVideoOrNot(courseChapter)
        for sectionLeafList in courseChapter.get('section_leaf_list', []):
            appendVideoOrNot(sectionLeafList)
            for leafList in sectionLeafList.get('leaf_list', []):
                appendVideoOrNot(leafList)
    return videoList


def getVideoRealId(urlId):
    """通过video在url中的id获取video的真实id"""
    response = launct1request(f'https://{Config["Domain"]}/mooc-api/v1/lms/learn/leaf_info/{Config["CourseId"]}/{urlId}/?sign={Config["Sign"]}&uv_id={Config["uv_id"]}')
    print(response)
    return response.json()['data']['content_info']['media']['ccid']


def save1video_video(realId, videoName):
    """保存一个视频的视频部分（不含字幕）"""
    print('正在下载视频')
    response = launct1request(f'https://{Config["Domain"]}/api/open/audiovideo/playurl?video_id={realId}&provider=cc&is_single=0')  # provider=cc意义暂不明确但是不可删除  is_single=0删除的话只会返回一个视频地址
    print(response)
    videoList = response.json()['data']['playurl']['sources']

    def chooseBestQuality(videoList):
        """
        如果videoList为 ['quality10': 'https://....', 'quality20': 'https://..']
        则返回 quality20
        """
        maxNum = -1
        ans = ''
        for thisQuality in videoList:
            thisNum = 0
            for c in thisQuality:
                if ord('0') <= ord(c) <= ord('9'):
                    thisNum = thisNum * 10 + ord(c) - ord('0')
            if thisNum > maxNum:
                maxNum = thisNum
                ans = thisQuality
        return ans
    
    bestQuality = chooseBestQuality(videoList)
    bestVideoUrl = videoList[bestQuality][0]
    response = launct1request(bestVideoUrl)
    print(response)
    videoNameWithPath = os.path.join(Config['SaveDirName'], videoName)
    with open(videoNameWithPath, 'wb') as f:
        f.write(response.content)


def save1video_srt(realId, srtName):
    """
    保存一个视频的字幕
    """
    response = launct1request(f'https://{Config["Domain"]}/api/open/yunpan/video/subtitle/list?cc_id={realId}')
    print(response)
    try:
        srtUrl = response.json()['data']['items'][0]['url']
    except:
        print('暂无字幕')
        return
    print('正在下载字幕')
    response = launct1request(srtUrl)
    print(response)
    srtNameWithPath = os.path.join(Config['SaveDirName'], srtName)
    with open(srtNameWithPath, 'wb') as f:
        f.write(response.content)


def save1video(urlId, videoName):
    """保存一个视频（视频 + 字幕）"""
    for cannotChar in '\\/:*?"<>|':  # 不能作为文件名的字符
        videoName.replace(cannotChar, '')
    videoName.replace(' ', '_')  # 将空格替换为下划线
    print(f'Saving Video {videoName}')
    realId = getVideoRealId(urlId)
    save1video_video(realId, videoName + '.mp4')
    save1video_srt(realId, videoName + '.srt')


def main():
    videoList = getVideoList()
    if not os.path.exists(Config['SaveDirName']):
        os.mkdir(Config['SaveDirName'])
    for videoNum, thisVideo in enumerate(videoList):
        save1video(thisVideo['urlId'], f'{videoNum:03d}_{thisVideo["videoName"].strip()}')
    print('All Finished...')


if __name__ == '__main__':
    main()
