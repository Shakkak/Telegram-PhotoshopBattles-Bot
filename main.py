import praw #if u have questions about praw read  https://www.storybench.org/how-to-scrape-reddit-with-python/ 
import requests
from bs4 import BeautifulSoup
import re
import time
import os
import logging
from telegram import ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,ForceReply
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

FILTER, TOP ,TYPING_REPLY,Limit_Submissions2= range(4)



def previewImage(submission): #previewImage post
    image_link = submission.preview["images"][0]['source']['url']
    return image_link

def captioncomment(text): #this function can expand to gather more links
    formats = ["jpg", "png", "jpeg", "peg", "mp4", "gif"]        
    if ("[" in text and "]" in text) and ("(" in text and ")" in text):
        count = 0
        for i in text:
            if i ==']':
                save1 = count
            if i == '(':
                save2a = count
            if i ==")":
                save2b = count            
            count += 1

        LINK_Image = text[save2a+1:save2b]
        Caption = text[1:save1]
        return Caption,LINK_Image
        
                    
    elif "https" in text and "imgur" in text:
        Flag = True
        s = re.search("https",text)
        for i in formats:
            e = re.search(i,text)
            if e != None:
                Flag = False
                break
        if Flag:
            e = re.search("/a/",text)
        test = e.start()+10
        if test != " " or test != "." or test != "!" or test != "?":
            test += 1
        link = text[s.start():test]
        Caption = text.replace(link, "")
        return Caption,link

    elif "https" in text:
        s = re.search("https",text)
        if "jpg" or "png" or "peg" or "mp4" or "gif" in text:
            for i in formats:
                e = re.search(i,text)
                if e != None:
                    end = e.start()+3
                    break
        elif "jpeg" in text:
            e = re.search("jpeg",text)
            end = e.start()+ 4
        link = text[s.start():end]
        Caption = text.replace(link, "")
        return Caption,link
    else:
        return None,None

def commentImage(submission,update,context,Comment_limited): #extract image link and the caption
    commentnumber = 1
    Chat_id = update.message.chat.id
    Flagbot = True
    error = 0
    for top_level_comment in submission.comments:
        try:
            time.sleep(1.1)
            if Flagbot:
                Flagbot = False
                continue
            if (commentnumber- error) == Comment_limited:
                break
            text = top_level_comment.body
            Caption, LINK_Image = captioncomment(text)
            LEN1 = len(text)
            LEN = 0
            if Caption != None:
                # "<a href='"+ link +"'>"+ text +"</a>" is a formula for hyperlink with the link for text 
                caption= "<a href='"+LINK_Image+"'>"+ str(top_level_comment.author)+": " +Caption +"</a>"+"\nupvotes: "+str(top_level_comment.score)+"    "+ str(commentnumber)
                LEN = len(LINK_Image)
                LEN1 = len(Caption)
            if Caption == None: # weird comment
                caption=str(top_level_comment.author) + ": " +text+"    "+ str(commentnumber) #use the defualt text in comment

            if text[LEN1-3:] == "jpg" or text[LEN1-3:] == "peg" or\
            text[LEN1-3:] == "png" or text[LEN1-4:] == "jpeg": #direct link
                b = re.search(r'\b(https)\b', text)
                if b.start() == 0:
                    context.bot.sendPhoto(chat_id=Chat_id, photo=text, caption=caption,parse_mode=ParseMode.HTML)
                    commentnumber += 1
                    continue
                else:
                    context.bot.sendPhoto(chat_id=Chat_id, photo=text[b.start():], caption=caption,parse_mode=ParseMode.HTML)
                    commentnumber += 1
                    continue
            elif LINK_Image[LEN-3:] == "jpg" or LINK_Image[LEN-3:] == "peg"\
            or LINK_Image[LEN-3:] == "png" or LINK_Image[LEN-4:] == "jpeg": #direct link - True
                b = re.search(r'\b(https)\b', LINK_Image)
                if b.start() == 0:
                    context.bot.sendPhoto(chat_id=Chat_id, photo=LINK_Image, caption=caption,parse_mode=ParseMode.HTML)
                    commentnumber += 1
                    continue
                else:
                    context.bot.sendPhoto(chat_id=Chat_id, photo=LINK_Image[b.start():], caption=caption,parse_mode=ParseMode.HTML)
                    commentnumber += 1
                    continue
            
            if text[LEN1-3:] =="mp4" or text[LEN1-3:] == "gif": #direct link
                context.bot.sendVideo(chat_id = Chat_id,video = text,caption=caption,parse_mode=ParseMode.HTML)
                commentnumber += 1
                continue  
            if LINK_Image[LEN-3:] == "mp4" or LINK_Image[LEN1-3:] == "gif": #direct link - True
                context.bot.sendVideo(chat_id = Chat_id,video = LINK_Image,caption=caption,parse_mode=ParseMode.HTML)
                commentnumber += 1
                continue
            else:
                if ("imgur" in LINK_Image) : #direct link - False
                    directlink = directlinkImgur(LINK_Image)
                    if directlink == None:
                        continue
                    if  "mp4" in directlink or "gif" in directlink:
                        context.bot.sendVideo(chat_id = Chat_id,video = directlink,caption=caption,parse_mode=ParseMode.HTML)
                    else:
                        context.bot.sendPhoto(chat_id=Chat_id, photo=directlink, caption=caption, parse_mode=ParseMode.HTML)
                    commentnumber += 1 
                
        except Exception as e:
            commentnumber += 1
            error += 1
            continue

  


def directlinkImgur(imageUrl): #scrap the direcet link

    data = requests.get(imageUrl)

    soup = BeautifulSoup(data.text,"html.parser")

    page_season = soup.find('meta',{'property':'og:image'})
    page_season = str(page_season)
    link =""
    page_season = page_season[15:55]
    count = 0
    for i in page_season:
        link = link + i
        if i == ".":
            count += 1
            if count == 3:
                break
    if "jpeg" in page_season :
        link = link + "jpeg"
    elif "jpg" in page_season:
        link = link + "jpg"
    elif "png" in page_season:
        link = link + "png"
    elif "mp4" in page_season:
        link = link + "mp4"
    elif "gif" in page_season:
        link = link + "gif"
    else:
        return None #image got deleted
    return link

def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their choice."""
    reply_keyboard = [['Hot Posts', 'Top Posts', 'New']]
    user = update.effective_user
    Starting_Massage = fr'Hi {user.mention_markdown_v2()}\! 👋'
    update.message.reply_markdown_v2(Starting_Massage)
    update.message.reply_text(

        'i can help u see PhotoshopBattles subreddit in a more simpler way! '
        'Send /cancel to stop talking to me.\n\n'
        'You always can choose /cancel in Menu!',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Which one?'
        ),
    )
    
    return FILTER


def filter(update: Update, context: CallbackContext) -> int:
    """Stores the selected filter and asks for a number of submissions."""
    """if filter was top filter it by time"""
    topic = update.message.text
    context.user_data['topic'] = topic

    if topic == "Hot Posts":
        update.message.reply_text(f'{topic.lower()}. how many submissions do u like to see? send your number 🧐\n\n'
            'Submissions are the orginal pictures. '
            'i will sort them by most upvotes.')
        return TYPING_REPLY

    if topic == "Top Posts":
        reply_keyboard = [['day', 'week', 'month','all']]

        update.message.reply_text(
        'Top of? ',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Top of?'
            ),
        )

        return TOP
    if topic == "New":
        update.message.reply_text(f'{topic.lower()}. how many submissions do u like to see? send your number 🧐\n\n'
            'Submissions are the orginal pictures. '
            'i will sort them by most upvotes.')
        return TYPING_REPLY
        

def topof_hot_new(update: Update, context: CallbackContext, dic) -> int:
    """hot/new with the limit of submissions and comments"""
    for i in dic.keys():
        if i == "submissions":
            Submissions_limited = int(dic[i])
        elif i == 'comment':
            Comment_limited = int(dic[i])
        elif i == "topic":
            Topic = dic[i]
    del dic["submissions"]
    del dic["comment"]
    del dic['topic']
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    Chat_id = update.message.chat.id
    if Topic == "Hot Posts":
        posts = reddit.subreddit('photoshopbattles').hot(limit=Submissions_limited+10)
    if Topic == "New":
        posts = reddit.subreddit('photoshopbattles').new(limit=Submissions_limited+10)
    Post_Number = 1
    for submission in posts:
        try:
            if (Post_Number-1) == Submissions_limited:
                break
            if submission.title[0:8] == "PsBattle":
                
                comments_number = len(submission.comments) - 1
                LinkOfPage = "https://www.reddit.com" + submission.permalink
                image_link = previewImage(submission)
                hyperlink = "<a href='"+LinkOfPage+"'>"+ submission.title +"</a>"
                if image_link == None:
                    continue

                context.bot.sendPhoto(chat_id=Chat_id, photo=image_link\
                  ,caption= hyperlink+"\nupvotes: "+str(submission.score)+ "\nnumber of comments: "+str(comments_number)\
                 +"\n#Orginal " + str(Post_Number),parse_mode=ParseMode.HTML)

                commentImage(submission,update,context,Comment_limited + 1)

                Post_Number += 1
        except Exception as e:
            continue


def topoftop(update: Update, context: CallbackContext, dic) -> int:
    """top with the limit of submissions and comments"""
    for i in dic.keys():
        if i == "choice":
            Time = dic[i]
        elif i == "submissions":
            Submissions_limited = int(dic[i])
        elif i == 'comment':
            Comment_limited = int(dic[i])

    del dic['choice']
    del dic["submissions"]
    del dic["comment"]
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    Chat_id = update.message.chat.id
    posts = reddit.subreddit('photoshopbattles').top(Time,limit=Submissions_limited+10)
    Post_Number = 1
    for submission in posts:
        # if (Post_Number - 1) == Submissions_limited :
        #     break
        try:
            
            if submission.title[0:8] == "PsBattle":
                if Post_Number <3:
                    Post_Number +=1
                    continue
                comments_number = len(submission.comments) - 1
                LinkOfPage = "https://www.reddit.com" + submission.permalink
                image_link = previewImage(submission)
                hyperlink = "<a href='"+LinkOfPage+"'>"+ submission.title +"</a>"
                if image_link == None:
                    continue

                context.bot.sendPhoto(chat_id=Chat_id, photo=image_link\
                  ,caption= hyperlink+"\nupvotes: "+str(submission.score)+ "\nnumber of comments: "+str(comments_number)\
                 +"\n#Orginal " + str(Post_Number),parse_mode=ParseMode.HTML)
                Post_Number += 1
                commentImage(submission,update,context, Comment_limited + 1)

        except Exception as e:
            continue




def Limit_Submissions(update: Update, context: CallbackContext) -> int:
    """limit submissions of Top."""
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'how many submissions do u like to see? send your number 🧐\n\n'
        'Submissions are the orginal pictures. '
        'i will sort them by most upvotes.')

    return TYPING_REPLY


def received_information(update: Update, context: CallbackContext) -> int:
    """Store number of submissions provided by user and ask for the comments."""
    if context.user_data['topic'] == "Top Posts":
        text = update.message.text
        context.user_data["submissions"] = text
        update.message.reply_text(
            "Maximum number of comments? send your number 🧐\n\n"
            "Comments are the photoshoped versions of the orginal submission.",
        )

        return Limit_Submissions2
    elif context.user_data['topic'] == "Hot Posts":
        text = update.message.text
        context.user_data["submissions"] = text
        update.message.reply_text(
            "Maximum number of comments? send your number 🧐\n\n"
            "Comments are the photoshoped versions of the orginal submission.",
        )
        return Limit_Submissions2
    elif context.user_data['topic'] == "New":
        text = update.message.text
        context.user_data["submissions"] = text
        update.message.reply_text(
            "Maximum number of comments? send your number 🧐\n\n"
            "Comments are the photoshoped versions of the orginal submission.",
        )
        return Limit_Submissions2

def received_information2(update: Update, context: CallbackContext) -> int:
    """Store number of comments provided"""
    if context.user_data['topic'] == "Top Posts":
        text = update.message.text
        context.user_data["comment"] = text

        update.message.reply_text(
            "Please Wait",
        )
        topoftop(update,context,context.user_data)
        cancel(update, context)
        return ConversationHandler.END

    elif context.user_data['topic'] == "Hot Posts" or context.user_data['topic'] == "New":
        text = update.message.text
        context.user_data["comment"] = text

        update.message.reply_text(
            "Please Wait",
        )
        topof_hot_new(update,context,context.user_data)
        cancel(update, context)
        return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! but remember, You always can /start over!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FILTER: [MessageHandler(Filters.regex('^(Hot Posts|Top Posts|New)$'), filter)],
            TOP: [MessageHandler(Filters.regex('^(day|week|month|all)$'), Limit_Submissions)],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command),
                    received_information,
                )
            ],
            Limit_Submissions2: [
                MessageHandler(
                    Filters.text & ~(Filters.command),
                    received_information2,
                )
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()