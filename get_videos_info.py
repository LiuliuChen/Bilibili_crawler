"""
Crawling data from Bilibili
API: bilibili_api https://github.com/LiuliuChen/bilibili-api
Author: Liuliu Chen
"""

import asyncio
import json
import os
from bilibili_api import video, Credential, comment, settings
from my_credential import SESSDATA, BILI_JCT, BUVID3
import utils

proxy = 'YOUR PROXY'
async def get_video_info(path, BVID, aid, sem):
    async with sem:
        try:
            # change proxy
            settings.proxy = proxy

            # 实例化 Credential 类
            credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
            # 实例化 Video 类
            v = video.Video(bvid=BVID)

            """get video basic info"""
            basic_info = await v.get_info()
            await asyncio.sleep(1)

            """get video stat"""
            stat = await v.get_stat()
            await asyncio.sleep(1)

            """get tags"""
            tags = await v.get_tags()
            await asyncio.sleep(1)

            """get pages info"""
            pages = await v.get_pages()
            await asyncio.sleep(1)

            """get download url of video"""
            download_urls = []
            for p in pages:
                d = await v.get_download_url(cid=p['cid'])
                await asyncio.sleep(2)
                download_urls.append(d)

            """get related info"""
            related_info = await v.get_related()
            await asyncio.sleep(1)
            # time.sleep(1)

            """get all comments"""
            # 存储评论
            comments = []
            hot_comments = []
            comments_stat = None
            # 页码
            page = 1
            # 当前已获取数量
            count = 0
            while True:
                # 获取评论
                try:
                    c = await comment.get_comments(aid, comment.ResourceType.VIDEO, page)
                    await asyncio.sleep(2)

                    # if page % 5 == 0:
                    #     time.sleep(1)

                    # store comments stat
                    if comments_stat is None:
                        comments_stat = c['page']
                    # 存储评论
                    comments.extend(c['replies'])
                    hot_comments.extend(c['hots'])
                    # 增加已获取数量
                    count += c['page']['size']
                    # 增加页码
                    page += 1

                    if count >= c['page']['count']:
                        # 当前已获取数量已达到评论总数，跳出循环
                        break

                except Exception as e:
                    if '12002' in str(e):
                        comments.append('评论区已关闭')
                    print('Error in comment page: ', page, ' ', e)
                    break

            video_info = {
                'basic_info': basic_info,
                'stat': stat,
                'tags': tags,
                'pages': pages,
                'download_url': download_urls,
                'related_info': related_info,
                'root_comment_list': comments,
                'hot_comment_list': hot_comments,
                'comment_stat': comments_stat
            }

            with open(path+'/'+BVID+'.json', 'w', encoding='utf-8') as f:
                json.dump(video_info, f, indent=2)

            print('finished: ', path.split('/')[-1], ' ', BVID, ' proxy: ', proxy)

        except Exception as e:
            err_msg = 'Failed in collecting: '+path.split('/')[-1]+' '+str(BVID)
            print(err_msg)
            print(e)
            print('Used proxy: ', proxy)
            with open('logs/video_info_error.txt', 'a', encoding='utf-8') as f:
                f.write(err_msg+'\n')
                f.write(str(e)+'\n')


def main():
    for root, dirs, files in os.walk('autodl-tmp/users/'):
        for f in files:
            if 'checkpoint' not in f:
                with open('autodl-tmp/users/'+f, 'r', encoding='utf-8') as f:
                    user = json.load(f)

                username = user['basic_info']['name']
                videos_list = user['videos_list']

                # creat a folder for the users
                path = 'autodl-tmp/videos/'+username
                if not os.path.exists(path):
                    os.makedirs(path)

                # get crawled videos for this user
                crawled_videos = utils.get_crawled(path)
                print(username, ' crawled videos: ', len(crawled_videos))

                # async
                tasks = []
                loop = asyncio.get_event_loop()
                # pool = ProxyPool(5)
                pool = None
                sem = asyncio.Semaphore(5)
                for v in videos_list:
                    # avoid crawling repeated video
                    if v['bvid'] not in crawled_videos:
                        task = asyncio.ensure_future(get_video_info(pool, path, v['bvid'], v['aid'], sem))
                        tasks.append(task)
                if tasks:
                    loop.run_until_complete(asyncio.wait(tasks))

                # # sync
                # pool = ProxyPool(5)
                # for v in videos_list:
                #     # avoid crawling repeated video
                #     if v['bvid'] not in crawled_videos:
                #         sync(get_video_info(pool, path, v['bvid'], v['aid'], sem))


if __name__ == '__main__':
    main()
