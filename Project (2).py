#Group Members
#M.Amaan Raza     465416
#Saad Ajmal       456490
#Asim Shah        470574
import feedparser
import string
import time
import threading
from project_util import translate_html
from datetime import datetime
import pytz
from tkinter import Frame, Scrollbar, Label, Text, Button, StringVar, END, BOTTOM, RIGHT, Y, TOP, Tk

# Problem 1: NewsStory Class
# Define a class to represent a news story with various attributes
class NewsStory:
    def __init__(self, guid, title, description, link, pubdate):
        self.guid = guid
        self.title = title
        self.description = description
        self.link = link
        self.pubdate = pubdate

    def get_guid(self):
        return self.guid

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def get_link(self):
        return self.link

    def get_pubdate(self):
        return self.pubdate

# Problem 2: Trigger Interface
# Define an abstract base class for triggers with an evaluate method to be overridden
class Trigger:
    def evaluate(self, story):
        raise NotImplementedError

# Problem 3: Phrase Trigger
# Define a class for phrase triggers to check if a phrase is in a given text
class PhraseTrigger(Trigger):
    def __init__(self, phrase):
        self.phrase = phrase.lower()

    def is_phrase_in(self, text):
        text = text.lower()
        for p in string.punctuation:
            text = text.replace(p, ' ')
        words = text.split()
        phrase_words = self.phrase.split()
        for i in range(len(words) - len(phrase_words) + 1):
            if phrase_words == words[i:i + len(phrase_words)]:
                return True
        return False

# Problem 4: TitleTrigger and DescriptionTrigger
# Define subclasses for title and description triggers
class TitleTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_title())

class DescriptionTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_description())

# Problem 5: Time Trigger
# Define a class for time-based triggers
class TimeTrigger(Trigger):
    def __init__(self, time_string):
        est = pytz.timezone("EST")
        self.time = est.localize(datetime.strptime(time_string, "%d %b %Y %H:%M:%S"))

class BeforeTrigger(TimeTrigger):
    def evaluate(self, story):
        return story.get_pubdate().replace(tzinfo=pytz.timezone("EST")) < self.time

class AfterTrigger(TimeTrigger):
    def evaluate(self, story):
        return story.get_pubdate().replace(tzinfo=pytz.timezone("EST")) > self.time

# Problem 6: Composite Triggers
# Define classes for combining triggers using logical operations
class NotTrigger(Trigger):
    def __init__(self, trigger):
        self.trigger = trigger

    def evaluate(self, story):
        return not self.trigger.evaluate(story)

class AndTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) and self.trigger2.evaluate(story)

class OrTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) or self.trigger2.evaluate(story)

# Problem 7: Filtering Stories
# Function to filter stories based on a list of triggers
def filter_stories(stories, triggerlist):
    filtered_stories = []
    for story in stories:
        for trigger in triggerlist:
            if trigger.evaluate(story):
                print(f"Trigger fired for story: {story.get_title()}")
                filtered_stories.append(story)
                break
    return filtered_stories

# Problem 8: Trigger Configuration
# Function to read the trigger configuration from a file
def read_trigger_config(filename):
    trigger_file = open(filename, 'r')
    lines = []
    for line in trigger_file:
        line = line.rstrip()
        if not (len(line) == 0 or line.startswith('//')):
            lines.append(line)
    trigger_file.close()

    triggers = {}
    triggerlist = []

    for line in lines:
        parts = line.split(",")
        if parts[0] == "ADD":
            for name in parts[1:]:
                triggerlist.append(triggers[name])
        else:
            trigger_name = parts[0]
            trigger_type = parts[1]
            if trigger_type == "TITLE":
                triggers[trigger_name] = TitleTrigger(parts[2])
            elif trigger_type == "DESCRIPTION":
                triggers[trigger_name] = DescriptionTrigger(parts[2])
            elif trigger_type == "BEFORE":
                triggers[trigger_name] = BeforeTrigger(parts[2])
            elif trigger_type == "AFTER":
                triggers[trigger_name] = AfterTrigger(parts[2])
            elif trigger_type == "NOT":
                triggers[trigger_name] = NotTrigger(triggers[parts[2]])
            elif trigger_type == "AND":
                triggers[trigger_name] = AndTrigger(triggers[parts[2]], triggers[parts[3]])
            elif trigger_type == "OR":
                triggers[trigger_name] = OrTrigger(triggers[parts[2]], triggers[parts[3]])

    return triggerlist

# Problem 9: Fetching and Processing RSS Feeds
# Function to fetch and process news from RSS feeds
def process(url):
    print(f"Fetching news from {url}")
    feed = feedparser.parse(url)
    entries = feed.entries
    ret = []
    for entry in entries:
        guid = entry.get('guid', '')
        title = translate_html(entry.get('title', ''))
        link = entry.get('link', '')
        description = translate_html(entry.get('description', ''))
        pubdate = translate_html(entry.get('published', ''))

        try:
            pubdate = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %Z")
            pubdate = pubdate.replace(tzinfo=pytz.timezone("GMT"))
            pubdate = pubdate.astimezone(pytz.timezone('EST'))
        except ValueError:
            try:
                pubdate = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %z")
                pubdate = pubdate.astimezone(pytz.timezone('EST'))
            except ValueError:
                pubdate = datetime.now(pytz.timezone('EST'))  # Default to current time if parsing fails

        newsStory = NewsStory(guid, title, description, link, pubdate)
        ret.append(newsStory)
    return ret

# Problem 10: Main Thread for GUI and Polling
# Function to set up the main thread for the GUI and polling the news feeds
SLEEPTIME = 120

def main_thread(master):
    try:
        t1 = TitleTrigger("election")
        t2 = DescriptionTrigger("Trump")
        t3 = DescriptionTrigger("Clinton")
        t4 = AndTrigger(t2, t3)
        triggerlist = [t1, t4]

        # Uncomment after implementing read_trigger_config
        # triggerlist = read_trigger_config('triggers.txt')

        frame = Frame(master)
        frame.pack(side=BOTTOM)
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT, fill=Y)

        t = "Google & Yahoo Top News"
        title = StringVar()
        title.set(t)
        ttl = Label(master, textvariable=title, font=("Helvetica", 18))
        ttl.pack(side=TOP)
        cont = Text(master, font=("Helvetica", 14), yscrollcommand=scrollbar.set)
        cont.pack(side=BOTTOM)
        cont.tag_config("title", justify='center')
        button = Button(frame, text="Exit", command=root.destroy)
        button.pack(side=BOTTOM)
        guidShown = []

        def get_cont(newstory):
            if newstory.get_guid() not in guidShown:
                cont.insert(END, newstory.get_title() + "\n", "title")
                cont.insert(END, "\n---------------------------------------------------------------\n", "title")
                cont.insert(END, newstory.get_description())
                cont.insert(END, "\n*********************************************************************\n", "title")
                guidShown.append(newstory.get_guid())

        while True:
            print("Polling . . .", end=' ')
            stories = process("http://news.google.com/news?output=rss")
            stories.extend(process("http://news.yahoo.com/rss/topstories"))

            stories = filter_stories(stories, triggerlist)
            list(map(get_cont, stories))
            scrollbar.config(command=cont.yview)

            print("Sleeping...")
            time.sleep(SLEEPTIME)

    except Exception as e:
        print(e)

if __name__ == '__main__':
    root = Tk()
    root.title("Some RSS parser")
    t = threading.Thread(target=main_thread, args=(root,))
    t.start()
    root.mainloop()
