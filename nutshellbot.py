import re, praw, requests, os, glob
from bs4 import BeautifulSoup

def download_Image(imageUrl, localFileName):
    response = requests.get(imageUrl)
    if response.status_code == 200:
        print('Downloading %s...' % (localFileName))
        with open(localFileName, 'wb') as fo:
            for chunk in response.iter_content(4096):
                fo.write(chunk)

def get_Image(submission):
    imgurUrlPattern = re.compile(r'(http://i.imgur.com/(.*))(\?.*)?')

    if "imgur.com/" not in submission.url:
        return # skip non-imgur submissions
    if submission.score < 3:
        return # skip submissions that haven't even reached 100 (thought this should be rare if we're collecting the "hot" submission)
    if len(glob.glob('reddit_%s_*' % (submission.id))) > 0:
        return # we've already downloaded files for this reddit submission

    if 'http://imgur.com/a/' in submission.url:
        # This is an album submission.
        albumId = submission.url[len('http://imgur.com/a/'):]
        htmlSource = requests.get(submission.url).text

        soup = BeautifulSoup(htmlSource)
        matches = soup.select('.album-view-image-link a')
        for match in matches:
            imageUrl = match['href']
            if '?' in imageUrl:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('?')]
            else:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:]
            localFileName = 'reddit_%s_album_%s_imgur_%s' % (submission.id, albumId, imageFile)
            download_Image('http:' + match['href'], localFileName)

    elif 'http://i.imgur.com/' in submission.url:
        # The URL is a direct link to the image.
        mo = imgurUrlPattern.search(submission.url) # using regex here instead of BeautifulSoup because we are pasing a url, not html

        imgurFilename = mo.group(2)
        if '?' in imgurFilename:
            # The regex doesn't catch a "?" at the end of the filename, so we remove it here.
            imgurFilename = imgurFilename[:imgurFilename.find('?')]

        localFileName = 'reddit_%s_album_None_imgur_%s' % (submission.id, imgurFilename)
        download_Image(submission.url, localFileName)

    elif 'http://imgur.com/' in submission.url:
        # This is an Imgur page with a single image.
        htmlSource = requests.get(submission.url).text # download the image's page
        soup = BeautifulSoup(htmlSource)
        imageUrl = soup.select('.image a')[0]['href']
        if imageUrl.startswith('//'):
            # if no schema is supplied in the url, prepend 'http:' to it
            imageUrl = 'http:' + imageUrl
        imageId = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('.')]

        if '?' in imageUrl:
            imageFile = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('?')]
        else:
            imageFile = imageUrl[imageUrl.rfind('/') + 1:]

        localFileName = 'reddit_%s_album_None_imgur_%s' % (submission.id, imageFile)
        download_Image(imageUrl, localFileName)

r = praw.Reddit(user_agent='example')

submissions = list(r.search('nutshell site:imgur.com', sort='new'))
for s in submissions:
    get_Image(s)

    
