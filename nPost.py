import os
import json
import re
import datetime
import urllib.request
import mimetypes
import xmltodict
import pytz
from urllib import parse
from collections import OrderedDict


class NPOST:
    """
    네이버 포스트로 포스팅 송출할 수 있도록 도와주는 클래스


    :param string login_id: 네이버 사용자 아이디
    :param string login_pw: 네이버 사용자 패스워드
    :param string uid: 네이버 포스트 등록 중 사용되는 고유 아이디
    """

    def __init__(self, login_id, login_pw, uid=''):
        self.cookies = ''
        self.status = ''
        self.uid = uid  # 단체 아이디 사용시 필요

        if not uid:
            self.uid = login_id

        self.login(login_id, login_pw)

    def login(self, login_id, login_pw):
        """
        네이버 로그인 처리 후 Cookies 획득

        :param string login_id: 네이버 사용자 아이디
        :param string login_pw: 네이버 사용자 패스워드
        :return: none
        """

        url = self.get_request_url('login')

        # 네이버 로그인을 위한 매개변수
        data = {'id': login_id, 'pw': login_pw, 'saveID': '0', 'enctp': '2', 'smart_level': '-1', 'svctype': '0'}
        data = parse.urlencode(data)
        bin_data = data.encode('utf-8')

        request = urllib.request.Request(url, data=bin_data, method='POST')

        # header 설정
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        request.add_header('Referer', 'https://nid.naver.com/nidlogin.login?'
                                      'svctype=262144&url=http://m.naver.com/aside/')
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/51.0.2704.103 Safari/537.36')

        response = urllib.request.urlopen(request)
        response_content = response.read().decode('utf-8')

        if response.status is 200:
            if self.get_request_url('loginSuccess') in response_content:
                # 쿠키 획득
                self.cookies = response.getheader('Set-cookie')
                self.status = 'ok'
            else:
                self.status = 'error'
        else:
            self.status = 'error'

    def send_post(self, pre_content, content, mode):
        """
        네이버로 포스팅할 데이터를 전송.
        포스트 요약본 데이터를 먼저 전송 후 포스트 전체 데이터를 전송.

        **mode**:
            - writePost : 등록
            - updatePost : 갱신

        :param json pre_content: 포스트 요약본 object
        :param json content: 포스트 object
        :param string mode: 등록 구분
        :return: 등록 처리결과 response
        """

        pre_url = self.get_request_url('prePost')
        post_url = self.get_request_url(mode)

        pre_data = pre_content.encode('euc-kr')

        request = urllib.request.Request(pre_url, data=pre_data, method='POST')

        # header 설정
        request.add_header('Referer', self.get_request_url('send'))
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/51.0.2704.103 Safari/537.36')
        request.add_header('Content-Type', 'application/json; charset=UTF-8')
        request.add_header('Cookie', self.cookies)

        urllib.request.urlopen(request)

        # 포스트 본문 전송

        post_data = content.encode('euc-kr')

        request = urllib.request.Request(post_url, data=post_data, method='POST')

        # header 설정
        request.add_header('Referer', self.get_request_url('canvas'))
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/51.0.2704.103 Safari/537.36')
        request.add_header('Content-Type', 'application/json; charset=UTF-8')
        request.add_header('Cookie', self.cookies)

        response = urllib.request.urlopen(request)

        response_content = json.loads(response.read().decode('utf-8'))

        return response_content

    def get_sessionkey(self):
        """
        현재 로그인한 사용자의 포스트 서비스 sessionKey 획득.

        :return: sessionKey
        """

        url = self.get_request_url('sessionKey')

        data = dict(uploaderType='simple', userId=self.uid, serviceId='post')
        data = parse.urlencode(data)
        bin_data = data.encode('utf-8')

        request = urllib.request.Request(url, data=bin_data, method='POST')

        # header 설정
        request.add_header('Referer', self.get_request_url('canvas'))
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/51.0.2704.103 Safari/537.36')

        request.add_header('Cookie', self.cookies)

        response = urllib.request.urlopen(request)
        response_content = json.loads(response.read().decode('utf-8'))
        session_key = response_content['result']['sessionKey']

        return session_key

    def get_tvcast_link_info(self, video_url):
        """
        입력된 TV 캐스트 영상 URL에서 해당영상의 정보를 가져온다.

        :param string video_url: TV 캐스트 영상 URL
        :return: TV 캐스트 영상 정보 json object
        """

        url = self.get_request_url('tvCast')
        referer = 'http://uploader1.nmv.naver.com/upload/linkNew.nhn?sid=26&userId=' + self.uid + '&tab=link'

        data = dict(url=video_url, serviceId=26, level='new')
        data = parse.urlencode(data)
        bin_data = data.encode('utf-8')

        request = urllib.request.Request(url, data=bin_data, method='POST')

        request.add_header('Referer', referer)
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/51.0.2704.103 Safari/537.36')
        request.add_header('cookie', self.cookies)

        response = urllib.request.urlopen(request)
        link_info = json.loads(response.read().decode('utf-8'))

        return link_info

    def get_related_article_meta_tag(self, url):
        """
        URL의 문서로 부터 사용된 facebook open graph meta tags 정보를 가져온다.

        :param string url: 관련기사 URL
        :return: facebook open graph meta tags
        """

        response = urllib.request.urlopen(url)
        response = response.read()
        response = response.decode('euc-kr', 'replace')

        tags = re.findall('<\s*meta\s+property="(og:[^"]+)"\s+content="([^"]*)', response)

        ogtags = {}
        for idx in range(len(tags)):
            ogtags[tags[idx][0]] = tags[idx][1]

        return ogtags

    def get_request_url(self, request_type):
        """
        해당 유형에 맞는 URL을 반환한다.

        :param string request_type: 액션 TYPE
        :return: URL
        """
        url_map = {
            'login': 'https://nid.naver.com/nidlogin.login',
            'loginSuccess': 'https://nid.naver.com/login/sso/finalize.nhn',
            'tvCast': 'http://uploader1.nmv.naver.com/upload/getLinkInfo.nhn',
            'sessionKey': 'http://post.editor.naver.com/PhotoUploader/SessionKey.json',
            'prePost': 'http://post.editor.naver.com/Service/PwmFilter.json',
            'writePost': 'http://post.editor.naver.com/documents/write.json',
            'updatePost': 'http://post.editor.naver.com/documents/update.json',
            'canvas': 'http://post.editor.naver.com/editor/canvas?serviceId=post',
            'send': 'http://post.editor.naver.com/editor',
        }

        return url_map.get(request_type)

    def send_image_file(self, file):
        """
        네이버로 이미지 파일 업로드
        (현재는 이미지 URL만 테스트 완료됨)

        :param file: 이미지 파일 또는 이미지 URL
        :return: 업로드 처리결과 response
        """

        session_key = self.get_sessionkey()
        url = 'http://ecommerce.upphoto.naver.com/' + session_key + '/simpleUpload/0'

        # file 이 url 인지 binary 인지 확인
        if type(file) == str:
            path = parse.urlparse(file).path
            ext = file.split('.')[-1]
            req = urllib.request.urlopen(file)
            f = req.read()
        else:
            f = file
            tmp_file = open(f)
            path = tmp_file.name
            ext = os.path.split(path)[1]

        content_type = 'image/' + ext
        fname = os.path.basename(path)

        response = self.post_multipart_file(url, f, fname, content_type)

        response = xmltodict.parse(response)
        response = json.dumps(response)
        response = json.loads(response)

        return response['item']

    def post_multipart_file(self, url, file, filename, content_type):

        referer = self.get_request_url('canvas')

        fields = {
            'userId': self.uid,
            'extractExif': 'False',
            'extractAnimatedCnt': 'True',
            'autorotate': 'True',
            'extractDominantColor': 'False'
        }

        files = [
            ('image', filename, file)
        ]

        cont_type, body = self.encode_multipart_formdata(fields, files)

        request = urllib.request.Request(url, data=body, method='POST')

        request.add_header('Referer', referer)
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/51.0.2704.103 Safari/537.36')
        request.add_header('Content-Type', cont_type)
        request.add_header('content-length', str(len(body)))
        request.add_header('cookie', self.cookies)

        response = urllib.request.urlopen(request)

        return response.read().decode('utf-8')

    def encode_multipart_formdata(self, fields, files):
        """
        이미지 업로드시 사용할 파일의 multipart data 생성

        :param fields: 전송할 파일정보
        :param files: not use
        :returns: content-type, multipart data
        """
        boundary_str = '------WebKitFormBoundarytZtQBX0ACVJGXe1W'
        crlf = bytes("\r\n", "ASCII")
        line = []

        for (key, value) in fields.items():
            line.append(bytes("--" + boundary_str, "ASCII"))
            line.append(bytes('Content-Disposition: form-data; name="%s"' % key, "ASCII"))
            line.append(b'')
            line.append(bytes(value, "ASCII"))
        for (key, filename, value) in files:
            line.append(bytes('--' + boundary_str, "ASCII"))
            line.append(bytes('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename), "ASCII"))
            line.append(bytes('Content-Type: %s' % self.get_content_type(filename), "ASCII"))
            line.append(b'')
            line.append(value)

        line.append(bytes('--' + boundary_str + '--', "ASCII"))
        line.append(b'')

        body = crlf.join(line)
        content_type = 'multipart/form-data; boundary=' + boundary_str

        return content_type, body

    def get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def get_youtube_video_info(self, url):
        """
        youtube 영상 아이디와 대표 썸네일 이미지 URL을 반환한다.

        **Support URL Patterns**:
            - http://youtu.be/SA2iWivDJiE
            - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
            - http://www.youtube.com/embed/SA2iWivDJiE
            - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US

        :param string url: youtube 영상 URL
        :return: 영상 아이디 썸네일 이미지 URL
        """
        mid = None
        query = parse.urlparse(url)
        if query.hostname == 'youtu.be':
            mid = query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse.parse_qs(query.query)
                mid = p['v'][0]
            if query.path[:7] == '/embed/':
                mid = query.path.split('/')[2]
            if query.path[:3] == '/v/':
                mid = query.path.split('/')[2]

        # thumbnail path
        path = 'http://img.youtube.com/vi/' + mid + '/maxresdefault.jpg'

        return mid, path

    def gen_preview_block(self, content):
        """
        미리보기 block 생성

        :param string content: 요약본문
        :return: preview block dictionary
        """
        content = content.replace("‘", "'")
        content = content.replace("’", "'")

        prev_obj = {}
        prev_obj['serviceId'] = 'post'
        prev_obj['ugcType'] = ['UGC100', 'UGC101', 'UGC102', 'UGC103', 'UGC013']
        prev_obj['content'] = content

        return prev_obj

    def gen_info_block(self, title):
        """
        포스트 기본 정보 block 생성

        :param string title: 제목
        :return: info block dictionary
        """

        # 현재시간
        date_format = "%Y-%m-%dT%H:%M:%S%z"
        now = datetime.datetime.now(pytz.timezone('Asia/Seoul')).strftime(date_format)

        info_obj = {}
        info_obj['serviceId'] = 'post'
        info_obj['document'] = {}
        info_obj['document']['docType'] = 'normal'
        info_obj['document']['title'] = title
        info_obj['document']['thumbnail'] = ''  # 용도를 알 수 없음
        info_obj['document']['theme'] = 'default'
        info_obj['document']['author'] = ''  # 용도를 알 수 없음
        info_obj['document']['publishDate'] = now  # ISO8601 format ex) 2016-08-01T10:14:45+09:00
        info_obj['document']['documentStyle'] = {'@ctype': 'documentStyle'}

        return info_obj

    def gen_title_header_block(self, title):
        """
        제목 영역 block 생성

        :param string title: 제목
        :return: Title Header Dictionary
        """
        header_obj = {}
        header_obj['title'] = title
        header_obj['publishDate'] = '1970-01-01T00:00:00.000+0000'  # 등록에 영향을 주지 않음
        header_obj['background'] = {}
        header_obj['background']['@ctype'] = 'background'
        header_obj['background']['color'] = ''
        header_obj['@ctype'] = 'documentTitle'
        header_obj['layout'] = 'default'
        header_obj['isFocused'] = 'false'
        header_obj['componentStyle'] = {}
        header_obj['componentStyle']['@ctype'] = 'componentStyle'
        header_obj['componentStyle']['align'] = 'left'
        header_obj['componentStyle']['fontFamily'] = 'nanumgothic'
        header_obj['componentStyle']['fontSize'] = 'D1'
        header_obj['componentStyle']['fontBold'] = False
        header_obj['componentStyle']['fontUnderline'] = False
        header_obj['componentStyle']['fontItalic'] = False
        header_obj['compId'] = 'documentTitle_9022535151470014076389'
        header_obj['focusComp'] = False

        return header_obj

    def gen_paragraph_block(self, text):
        """
        본문 text block 생성

        :param string text: 내용
        :return: Paragraph Block Dictionary
        """

        if not text:
            text = ''

        paragraph_obj = {}
        paragraph_obj['value'] = text
        paragraph_obj['@ctype'] = 'paragraph'
        paragraph_obj['layout'] = 'default'
        paragraph_obj['isFocused'] = False
        paragraph_obj['componentStyle'] = {}
        paragraph_obj['componentStyle']['@ctype'] = 'componentStyle'
        paragraph_obj['componentStyle']['align'] = 'left'
        paragraph_obj['componentStyle']['fontFamily'] = 'nanumgothic'
        paragraph_obj['componentStyle']['fontSize'] = 'T3'
        paragraph_obj['componentStyle']['fontBold'] = False
        paragraph_obj['componentStyle']['fontUnderline'] = False
        paragraph_obj['componentStyle']['fontItalic'] = False
        paragraph_obj['componentStyle']['lineHeight'] = ''
        paragraph_obj['compId'] = 'paragraph_3801062811469603612800'
        paragraph_obj['focusComp'] = False

        return paragraph_obj

    def gen_section_title_block(self, subtitle):
        """
        중간 제목 block 생성

        :param string subtitle: 중간제목
        :return: 중간제목 block Dictionary
        """

        # 특수문자 제거 (필요시 reg 추가하여 처리)
        #subtitle = re.sub(r'◆', '', subtitle)

        subtitle_obj = {}
        subtitle_obj['value'] = subtitle.strip()
        subtitle_obj['@ctype'] = 'quotation'
        subtitle_obj['layout'] = 'default'
        subtitle_obj['isFocused'] = False
        subtitle_obj['componentStyle'] = {}
        subtitle_obj['componentStyle']['@ctype'] = 'componentStyle'
        subtitle_obj['componentStyle']['fontSize'] = 'T2'
        subtitle_obj['componentStyle']['fontBold'] = False
        subtitle_obj['componentStyle']['fontUnderline'] = False
        subtitle_obj['componentStyle']['fontItalic'] = False
        subtitle_obj['compId'] = 'quotation_2711786871470204596536'
        subtitle_obj['focusComp'] = False

        return subtitle_obj

    def gen_image_block(self, image, represent):
        """
        image block 생성

        **represent**:
            - False : 일반 이미지
            - True : 대표 이미지

        :param image: image URL 또는 file
        :param represent: 대표이미지 여부,
        :return: 이미지 Block Dictionary
        """
        img_obj = {}
        img_obj['src'] = 'http://post.phinf.naver.net' + image['url'] + '?type=w1200'
        img_obj['width'] = image['width']
        img_obj['height'] = image['height']
        img_obj['originalWidth'] = image['width']
        img_obj['originalHeight'] = image['height']
        img_obj['alt'] = image['fileName']
        img_obj['caption'] = ''

        if 'naCaption' in image:  # 캡션이 있다면 추가
            img_obj['caption'] = image['naCaption']

        img_obj['path'] = image['thumbnail']
        img_obj['domain'] = 'http://post.phinf.naver.net/'
        img_obj['uploadedLocal'] = True
        img_obj['offsetCenterXRatio'] = 0
        img_obj['offsetCenterYRatio'] = 0
        img_obj['backgroundPositionX'] = '50%'
        img_obj['backgroundPositionY'] = '50%'
        img_obj['fileSize'] = image['fileSize']
        img_obj['represent'] = represent
        img_obj['fileName'] = image['fileName']
        img_obj['animationGif'] = False

        if 'gallery_link' in image:  # 화보라면 링크 처리
            img_obj['link'] = image['gallery_link']

        img_obj['@ctype'] = 'image'
        img_obj['layout'] = 'default'
        img_obj['isFocused'] = False
        img_obj['componentStyle'] = {}
        img_obj['componentStyle']['@ctype'] = 'componentStyle'
        img_obj['componentStyle']['align'] = 'justify'
        img_obj['componentStyle']['fontBold'] = False
        img_obj['componentStyle']['fontUnderline'] = False
        img_obj['componentStyle']['fontItalic'] = False
        img_obj['compId'] = 'image_5233948931470204596538'
        img_obj['focusComp'] = False

        return img_obj

    def gen_video_block(self, info, mtype):
        """
        video block 생성

        **mtype**:
            - tvCast : 네이버 TV캐스트 영상
            - youtube : Youtube 영상

        :param string info: 영상관련 정보
        :param string mtype: 영상 종류
        :return: 영상 Block Dictionary
        """
        video = {}

        if mtype == 'tvCast':  # TVCast 영상일 경우
            video['vid'] = info['videoId']
            video['caption'] = ''
            video['thumbnail'] = {}
            video['thumbnail']['@ctype'] = 'simpleThumbnail'
            video['thumbnail']['src'] = info['thumbnail']
            video['thumbnail']['alt'] = info['title']
            video['source'] = info['videoTemplateSource']
            video['template'] = info['videoTemplate']
            video['vender'] = 'TVcast'
        else:  # 유튜브 영상일 경우
            # vid and thumbnail url parse
            vid, thumb_url = self.get_youtube_video_info(info['src'])

            video['vid'] = vid
            video['caption'] = ''
            video['thumbnail'] = {}
            video['thumbnail']['@ctype'] = 'simpleThumbnail'
            video['thumbnail']['src'] = thumb_url
            video['thumbnail']['alt'] = ''
            video['source'] = info['src']
            video['template'] = info['html']
            video['vender'] = 'youtube'

        video['@ctype'] = 'video'
        video['layout'] = 'default'
        video['isFocused'] = False
        video['uploadedLocal'] = True
        video['represent'] = False
        video['fileSize'] = 0
        video['componentStyle'] = {}
        video['componentStyle']['@ctype'] = 'componentStyle'
        video['componentStyle']['fontBold'] = False
        video['componentStyle']['fontUnderline'] = False
        video['componentStyle']['fontItalic'] = False
        video['compId'] = 'video_7546429391470204596539'
        video['focusComp'] = False

        return video

    def gen_byline_block(self, name, email):
        """
        바이라인 block 생성

        :param string name: 작성자명
        :param string email: 작성자 이메일
        :return: 바이라인 Block Dictionary
        """

        value = '<span style="color: rgb(0, 0, 0);' \
                '">' + name + '</span><span class="Apple-converted-space" ' \
                'style="color: rgb(0, 0, 0);">&nbsp;</span>' \
                '<a href="mailto:' + email + '" style="color: rgb(96, 140, 186) ' \
                '!important">' + email + '</a><span class="Apple-converted-space" ' \
                'style="color: rgb(0, 0, 0);"></span><span style="color: rgb(0, 0, 0);">' \
                '&lt;Your Company(</span><a href="http://YourComapany.com/" target="_blank" ' \
                'style="color: rgb(96, 140, 186) !important">http://YourCompany.com</a><span style="color:' \
                ' rgb(0, 0, 0);">) &gt;</span></br>'

        byline = OrderedDict()
        byline['value'] = value
        byline['@ctype'] = 'paragraph'
        byline['layout'] = 'default'
        byline['isFocused'] = False
        byline['componentStyle'] = OrderedDict()
        byline['componentStyle']['@ctype'] = 'componentStyle'
        byline['componentStyle']['align'] = 'left'
        byline['componentStyle']['fontFamily'] = 'nanumgothic'
        byline['componentStyle']['fontSize'] = 'T3'
        byline['componentStyle']['fontBold'] = False
        byline['componentStyle']['fontUnderline'] = False
        byline['componentStyle']['fontItalic'] = False
        byline['componentStyle']['lineHeight'] = ''
        byline['compId'] = 'paragraph_3801062811469603612800'
        byline['focusComp'] = False

        return byline

    def gen_related_article_block(self, tags):
        """
        관련기사 block 생성

        :param dictionary tags: facebook og tags
        :return: 관련기사 Block Dictionary
        """
        rel_object = OrderedDict()
        rel_object['title'] = tags['og:title']
        rel_object['link'] = tags['og:url']
        rel_object['domain'] = 'www.motorgraph.com'
        rel_object['thumbnail'] = OrderedDict()
        rel_object['thumbnail']['@ctype'] = 'thumbnail'
        rel_object['thumbnail']['src'] = tags['og:image']
        rel_object['thumbnail']['width'] = tags['og:image:width']
        rel_object['thumbnail']['height'] = tags['og:image:height']
        rel_object['desc'] = tags['og:description']
        rel_object['isVideo'] = False
        rel_object['@ctype'] = 'oglink'
        rel_object['layout'] = 'og_bSize'
        rel_object['isFocused'] = False
        rel_object['componentStyle'] = OrderedDict()
        rel_object['componentStyle']['@ctype'] = 'componentStyle'
        rel_object['componentStyle']['align'] = 'center'
        rel_object['compId'] = 'oglink_6562828561470302602492'
        rel_object['focusComp'] = False

        return rel_object

    def gen_meta_data_block(self, tags="", document_id=""):
        """
        포스트 기본 metadata block 생성

        :param string tags: 포스트에 들어가는 해쉬태그(필수 아님)
        :param string document_id: 문서 업데이트 시 사용되는 문서ID
        :return: metaData Block Dictionary
        """

        # 클라우드 태그 처리 (없다면 기본 태그 추가)
        if tags:
            cloudtags = tags.split(',')
            cloudtags = filter(None, cloudtags)
            cloudtags = list(cloudtags)
            #  ' ' item 제거 (empty item 과 다름)
            if ' ' in cloudtags:
                cloudtags.remove(' ')
            #  item 에 포함된 space 제거
            cloudtags = [x.strip(' ') for x in cloudtags]
            cloudtags = [x.replace(' ', '') for x in cloudtags]
        else:
            cloudtags = ['모터그래프']

        meta_obj = OrderedDict()
        meta_obj['doctype'] = 'normal'
        meta_obj['publishMeta'] = OrderedDict()
        meta_obj['publishMeta']['title'] = ''
        meta_obj['publishMeta']['templateType'] = 'UGC_SIMPLE'
        meta_obj['publishMeta']['volumeNo'] = -1
        meta_obj['publishMeta']['seriesNo'] = ''  # 시리즈에 추가 하려면 시리즈 코드를 획득하여 이곳에 넣는다
        meta_obj['publishMeta']['openType'] = 0   # 전체공개 여부 (0: 노출, 10: 비노출)
        meta_obj['publishMeta']['searchNotAllowed'] = 0  # 검색결과 노출여부 (0: 노출, 1: 비노출)
        meta_obj['publishMeta']['volumeAuthorComment'] = ''
        meta_obj['publishMeta']['reserveDate'] = ''  # 예약 발행 시 이곳에 날짜를 넣는다
        meta_obj['publishMeta']['blogpublish'] = False  # 연동된 블로그에 동시 발행 시 TRUE (테스트 해보지 않음)
        meta_obj['publishMeta']['facebookPublish'] = False  # 연동된 페이스북에 동시 발행 (테스트 해보지 않음)
        meta_obj['publishMeta']['blogCategoryNo'] = None  # 아마도 연동된 블로그의 카테고리
        meta_obj['publishMeta']['cloudTags'] = cloudtags  # 포스트에 들어가는 해쉬태그
        meta_obj['publishMeta']['status'] = ''
        meta_obj['publishMeta']['categoryNo'] = 57  # 포스트 카테고리 코드 (57은 자동차)
        meta_obj['publishMeta']['masterYn'] = True
        meta_obj['publishMeta']['docTemplateType'] = ''
        meta_obj['publishMeta']['@service'] = 'post'
        # 임시문서 아이디 (랜덤으로 하게 되면 다른 사용자의 문서가 훼손될 수도 있어서 문제가 될수도 있음
        meta_obj['publishMeta']['tempDocumentId'] = '27505684'

        # 신규 등록이 아닌 업데이트라면 documentId를 추가해줘야 함
        if bool(document_id):
            meta_obj['documentId'] = document_id

        return meta_obj
